from django.db.models import Count, F
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from station.models import Bus, Trip, Facility, Order
from station.permissions import IsAdminOrIFAuthenticatedReadOnly
from station.serializers import (
    BusSerializer,
    BusListSerializer,
    BusDetailSerializer,
    BusImageSerializer,
    TripSerializer,
    TripListSerializer,
    TripDetailSerializer,
    FacilitySerializer,
    OrderSerializer,
    OrderListSerializer,
)


class BusViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer
    permission_classes = (IsAdminOrIFAuthenticatedReadOnly,)

    @staticmethod
    def _params_to_ints(qs):
        return [int(param_id) for param_id in qs.split(",")]

    def get_queryset(self):
        queryset = self.queryset

        facilities = self.request.query_params.get("facilities")
        if facilities:
            facilities_ids = self._params_to_ints(facilities)
            queryset = queryset.filter(
                facilities__id__in=facilities_ids
            ).distinct()

        if self.action in ("list", "retrieve"):
            return queryset.prefetch_related("facilities")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return BusListSerializer

        if self.action == "retrieve":
            return BusDetailSerializer

        if self.action == "upload_image":
            return BusImageSerializer

        return self.serializer_class

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading picture to specific bus"""
        bus = self.get_object()
        serializer = self.get_serializer(bus, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Only for documentation purposes
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="facilities",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by facility id (ex. ?facilities=2,5)",
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = (IsAdminOrIFAuthenticatedReadOnly,)

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("bus").annotate(
                tickets_available=F("bus__num_seats") - Count("tickets")
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return TripListSerializer

        if self.action == "retrieve":
            return TripDetailSerializer

        return TripSerializer


class FacilityViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
    permission_classes = (IsAdminOrIFAuthenticatedReadOnly,)


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 50


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related("tickets__trip__bus")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
