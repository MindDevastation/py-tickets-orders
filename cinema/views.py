from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, OrderSerializer,
)

class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

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

    def get_queryset(self):
        queryset = super().get_queryset()

        actors = self.request.query_params.get("actors", None)
        if actors:
            actor_ids = [int(id) for id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actor_ids)

        genres = self.request.query_params.get("genres", None)
        if genres:
            genre_ids = [int(id) for id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genre_ids)

        title = self.request.query_params.get("title", None)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        date = self.request.query_params.get("date", None)
        if date:
            queryset = queryset.filter(show_time__date=date)

        movie_id = self.request.query_params.get("movie", None)
        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        return queryset
