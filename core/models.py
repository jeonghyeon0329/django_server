from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid

class Tenant(models.Model):
    """
    멀티테넌트의 최상위 엔터티(조직/고객 단위).
    다른 업무 테이블은 이 모델을 참조해 '어느 테넌트의 데이터인지'를 명시합니다.
    """
    code = models.SlugField(
        unique=True, max_length=50,
        verbose_name=_("테넌트 코드"),
        help_text=_("URL/서브도메인 등에 쓰는 슬러그(예: acme, foo-bar). 생성 후 변경을 피하는 것을 권장합니다."),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("테넌트 이름"),
        help_text=_("사람이 읽는 이름(회사/조직명)."),
    )

    class Meta:
        verbose_name = _("테넌트")
        verbose_name_plural = _("테넌트")
        indexes = [
            models.Index(fields=["name"], name="tenant_name_idx"),
        ]

    def __str__(self):
        return self.code


class TimestampedModel(models.Model):
    """
    생성/수정 시각을 공통 제공하는 추상 베이스 모델.
    """
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("생성 시각"),
        help_text=_("레코드가 생성된 시각입니다."),
        db_index=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("수정 시각"),
        help_text=_("레코드가 저장될 때마다 자동 갱신됩니다."),
    )

    class Meta:
        abstract = True


class TenantAwareModel(TimestampedModel):
    """
    '모든 레코드는 특정 테넌트에 속한다'는 계약을 강제하는 추상 베이스 모델.
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("소속 테넌트"),
        help_text=_("이 레코드가 속한 테넌트입니다. 테넌트 삭제 시 보호(PROTECT)됩니다."),
        db_index=True,
    )

    class Meta:
        abstract = True


class IdempotencyKey(models.Model):
    """
    멱등성 보장을 위한 키 저장소.
    동일 요청(재시도 등)에 대해 한 번만 처리하거나, 이전 응답을 재사용할 때 사용합니다.
    """
    key = models.CharField(
        max_length=200, unique=True,
        verbose_name=_("멱등 키"),
        help_text=_("클라이언트/게이트웨이에서 제공하는 멱등 키(X-Idempotency-Key 등). 유니크합니다."),
    )
    request_hash = models.CharField(
        max_length=200,
        verbose_name=_("요청 해시"),
        help_text=_("요청 바디/주요 파라미터의 해시. 동일 키 재사용 시 내용 일치 여부 검증에 사용."),
        db_index=True,
    )
    response_body = models.TextField(
        blank=True,
        verbose_name=_("응답 캐시"),
        help_text=_("이미 처리된 요청의 응답(JSON 직렬화 문자열 등)을 보관합니다."),
    )
    status_code = models.IntegerField(
        default=0,
        verbose_name=_("상태 코드"),
        help_text=_("처리 시의 HTTP 상태 코드(0=미처리/미정)."),
        db_index=True,
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("생성 시각"),
        help_text=_("키가 생성된 시각입니다. 보관 정책에 따라 정리하세요."),
        db_index=True,
    )

    class Meta:
        verbose_name = _("멱등 키")
        verbose_name_plural = _("멱등 키")
        ordering = ["-created_at"]
        constraints = [
            # status_code는 0(미정) 또는 100~599 범위 허용
            models.CheckConstraint(
                name="idemp_status_code_valid",
                check=(
                    models.Q(status_code=0) |
                    (models.Q(status_code__gte=100) & models.Q(status_code__lte=599))
                ),
            ),
        ]

    def __str__(self):
        return self.key


class Outbox(TenantAwareModel):
    """
    트랜잭션 아웃박스 패턴을 위한 큐 테이블.
    로컬 트랜잭션에 이벤트를 영속화하고, 퍼블리셔가 'published=False'만 폴링해 외부로 발행합니다.
    """
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
        verbose_name=_("ID"),
        help_text=_("이벤트 레코드의 전역 고유 식별자(UUID)."),
    )
    event_name = models.CharField(
        max_length=200,
        verbose_name=_("이벤트 이름"),
        help_text=_('예: "user.created", "invoice.paid" 등 이벤트 타입 식별자.'),
        db_index=True,
    )
    payload = models.JSONField(
        verbose_name=_("페이로드"),
        help_text=_("이벤트 본문(JSON). 스키마는 애플리케이션 계약으로 관리합니다."),
    )
    published = models.BooleanField(
        default=False,
        verbose_name=_("발행 여부"),
        help_text=_("퍼블리셔가 처리 완료하면 True로 마킹합니다."),
        db_index=True,
    )

    class Meta:
        verbose_name = _("아웃박스 이벤트")
        verbose_name_plural = _("아웃박스 이벤트")
        ordering = ["created_at"]
        indexes = [
            # 퍼블리셔 폴링/정리 작업 최적화를 위한 복합 인덱스
            models.Index(fields=["tenant", "published", "created_at"], name="outbox_poll_idx"),
            models.Index(fields=["tenant", "event_name", "published"], name="outbox_event_idx"),
        ]

    def __str__(self):
        return f"{self.event_name} ({self.id})"
