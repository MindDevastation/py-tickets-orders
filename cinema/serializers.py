from django.core.exceptions import ValidationError
from rest_framework import serializers

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Ticket, Order


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieListSerializer(MovieSerializer):
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    actors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )


class MovieDetailSerializer(MovieSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionListSerializer(MovieSessionSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )
    tickets_available = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "tickets_available",
        )

    def get_tickets_available(self, obj):
        total_capacity = obj.cinema_hall.capacity
        reserved_tickets = Ticket.objects.filter(movie_session=obj).count()
        available_tickets = total_capacity - reserved_tickets
        return available_tickets


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_seats = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_seats")

    def get_taken_seats(self, obj):
        return obj.taken_seats

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ('movie_session', 'row', 'seat', 'order')

    def validate_row(self, value):
        movie_session = self.initial_data.get("movie_session")
        cinema_hall = movie_session.cinema_hall
        if value < 1 or value > cinema_hall.rows:
            raise ValidationError(
                f"Row number must be between 1 and {cinema_hall.rows}."
            )
        return value

    def validate_seat(self, value):
        movie_session = self.initial_data.get("movie_session")
        cinema_hall = movie_session.cinema_hall
        if value < 1 or value > cinema_hall.seats_in_row:
            raise ValidationError(
                f"Seat number must be between 1 and {cinema_hall.seats_in_row}."
            )
        return value

    def validate(self, data):
        movie_session = data.get('movie_session')
        row = data.get('row')
        seat = data.get('seat')

        if Ticket.objects.filter(movie_session=movie_session, row=row, seat=seat).exists():
            raise ValidationError(
                f"The seat (row {row}, seat {seat}) is already taken for this movie session."
            )

        return data

class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)
    movie_session = MovieSessionListSerializer(source="tickets.movie_session", many=True)

    class Meta:
        model = Order
        fields = ("id", "created_at", "user", "tickets", "movie_session")

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")

        order = Order.objects.create(user=self.context['request'].user, **validated_data)

        for ticket_data in tickets_data:
            movie_session = ticket_data['movie_session']
            Ticket.objects.create(
                order=order,
                movie_session=movie_session,
                row=ticket_data['row'],
                seat=ticket_data['seat']
            )

        return order
