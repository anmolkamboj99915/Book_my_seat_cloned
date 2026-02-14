from django.contrib import admin
from .models import Movie, Theater, Seat, Booking


# ==================================================
# MOVIE ADMIN
# ==================================================

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['name', 'genre', 'language', 'rating']
    search_fields = ['name', 'genre', 'language']
    list_filter = ['genre', 'language']
    ordering = ['name']
    fields = [
        'name',
        'image',
        'rating',
        'genre',
        'language',
        'cast',
        'description',
        'trailer_url'
    ]


# ==================================================
# THEATER ADMIN
# ==================================================

@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ['name', 'movie', 'time']
    search_fields = ['name', 'movie__name']
    list_filter = ['movie']
    ordering = ['-time']


# ==================================================
# SEAT ADMIN
# ==================================================

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = [
        'theater',
        'seat_number',
        'is_booked',
        'is_reserved',
        'reserved_by',
        'reserved_at'
    ]
    list_filter = ['is_booked', 'is_reserved', 'theater']
    search_fields = ['seat_number', 'theater__name']
    ordering = ['theater', 'seat_number']
    readonly_fields = ['reserved_at']


# ==================================================
# BOOKING ADMIN
# ==================================================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'movie',
        'theater',
        'seat',
        'is_paid',
        'amount_paid',
        'booked_at'
    ]
    list_filter = ['is_paid', 'movie', 'theater']
    search_fields = ['user__username', 'movie__name', 'seat__seat_number']
    ordering = ['-booked_at']
    readonly_fields = ['booked_at']
