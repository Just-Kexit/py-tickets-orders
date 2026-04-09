from django.db.models import Q, Count, F
from rest_framework import viewsets

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order
)
from cinema.pagination import OrderSetPagination

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, OrderSerializer, OrderListSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    @staticmethod
    def _param_int(param):
        return int(param)

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = queryset.select_related().annotate(
                total_seats=F("cinema_hall__rows")
                * F("cinema_hall__seats_in_row")
            ).annotate(
                tickets_available=F("total_seats") - Count("tickets")
            )

            actors = self.request.query_params.get("actors")
            genres = self.request.query_params.get("genres")
            title = self.request.query_params.get("title")

            date = self.request.query_params.get("date")
            movie = self.request.query_params.get("movie")

            if actors:
                queryset = queryset.filter(
                    Q(movie__actors__first_name__icontains=actors)
                    | Q(movie__actors__last_name__icontains=actors)
                )

            if genres:
                queryset = queryset.filter(
                    movie__genres__name__icontains=genres
                )

            if title:
                queryset = queryset.filter(
                    movie__title__icontains=title
                )

            if date:
                queryset = queryset.filter(
                    show_time__date=date
                )

            if movie:
                movie = self._param_int(movie)
                queryset = queryset.filter(
                    movie_id=movie
                )

            if self.action == "retrieve":
                queryset = queryset.prefetch_related("movie")
        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__movie_session__movie",
                "tickets__movie_session__cinema_hall"
            )

        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "tickets__movie_session"
            )

        return queryset

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == "list":
            serializer_class = OrderListSerializer
        return serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
