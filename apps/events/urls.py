from django.urls import path

from apps.events.views import EventDetailView, EventListView, SeatListView

urlpatterns = [
    path("events/view/", EventListView.as_view(), name="event-list"),
    path("events/view/<int:pk>/", EventDetailView.as_view(), name="event-detail"),
    path("events/view/<int:pk>/seats/", SeatListView.as_view(), name="seat-list"),
]
