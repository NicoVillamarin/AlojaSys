from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RatePlanViewSet, RateRuleViewSet, preview_rate, preview_rate_range, rate_choices, PromoRuleViewSet, TaxRuleViewSet

router = DefaultRouter()
router.register(r"rate-plans", RatePlanViewSet, basename="rateplan")
router.register(r"rate-rules", RateRuleViewSet, basename="raterule")
router.register(r"promo-rules", PromoRuleViewSet, basename="promorule")
router.register(r"tax-rules", TaxRuleViewSet, basename="taxrule")

urlpatterns = [
    path("choices/", rate_choices, name="rates-choices"),
    path("preview-rate-range/", preview_rate_range, name="preview-rate-range"),
    path("preview-rate/", preview_rate, name="preview-rate"),
    path("", include(router.urls)),
]