from django.db import models
from django.contrib.auth.models import User
from urllib.parse import urlparse, parse_qs
from django.utils import timezone
from datetime import timedelta


# =========================
# MOVIE MODEL
# =========================
class Movie(models.Model):
    GENRE_CHOICES = [
        ("Action", "Action"),
        ("Comedy", "Comedy"),
        ("Drama", "Drama"),
        ("Thriller", "Thriller"),
        ("Horror", "Horror"),
        ("Romance", "Romance"),
    ]

    LANGUAGE_CHOICES = [
        ("English", "English"),
        ("Hindi", "Hindi"),
        ("Tamil", "Tamil"),
        ("Telugu", "Telugu"),
        ("Spanish", "Spanish"),
    ]

    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="movies/")
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    cast = models.TextField()
    description = models.TextField(blank=True, null=True)

    # ✅ NEW: Genre & Language
    genre = models.CharField(max_length=100, choices=GENRE_CHOICES, blank=True)
    language = models.CharField(max_length=100, choices=LANGUAGE_CHOICES, blank=True)

    # ✅ Trailer
    trailer_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    # ✅ Auto-convert any YouTube link to embed format
    def save(self, *args, **kwargs):
        if self.trailer_url:
            parsed_url = urlparse(self.trailer_url)
            video_id = None

            if "youtu.be" in parsed_url.netloc:
                video_id = parsed_url.path.lstrip('/')

            elif "youtube.com" in parsed_url.netloc:
                query = parse_qs(parsed_url.query)
                if "v" in query:
                    video_id = query["v"][0]
                elif "/embed/" in parsed_url.path:
                    video_id = parsed_url.path.split("/embed/")[-1]
                elif "/shorts/" in parsed_url.path:
                    video_id = parsed_url.path.split("/shorts/")[-1]

            if video_id:
                self.trailer_url = f"https://www.youtube.com/embed/{video_id}"

        super().save(*args, **kwargs)


# =========================
# THEATER MODEL
# =========================
class Theater(models.Model):
    name = models.CharField(max_length=255)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='theaters')
    time = models.DateTimeField()

    def __str__(self):
        return f'{self.name} - {self.movie.name} at {self.time}'


# =========================
# SEAT MODEL (User-Specific Reservation)
# =========================
class Seat(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=10)

    is_booked = models.BooleanField(default=False)

    # ✅ Temporary reservation system
    is_reserved = models.BooleanField(default=False)
    reserved_at = models.DateTimeField(blank=True, null=True)

    # ✅ NEW: Reserved by which user
    reserved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reserved_seats"
    )

    def is_reservation_expired(self):
        if self.is_reserved and self.reserved_at:
            return timezone.now() > self.reserved_at + timedelta(minutes=5)
        return False

    def __str__(self):
        return f'{self.seat_number} in {self.theater.name}'


# =========================
# BOOKING MODEL
# =========================
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    seat = models.OneToOneField(Seat, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)

    # ✅ Payment Tracking
    is_paid = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=255, blank=True, null=True)

    # ✅ Price for analytics
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Booking by {self.user.username} for {self.seat.seat_number}'
