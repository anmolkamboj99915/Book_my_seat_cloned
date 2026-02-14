from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Theater, Seat, Booking
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.core.mail import send_mail
from django.conf import settings
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


# =========================
# MOVIE LIST + FILTERS
# =========================
def movie_list(request):
    movies = Movie.objects.all()

    search_query = request.GET.get("search")
    genre = request.GET.get("genre")
    language = request.GET.get("language")

    if search_query:
        movies = movies.filter(name__icontains=search_query)

    if genre:
        movies = movies.filter(genre=genre)

    if language:
        movies = movies.filter(language=language)

    return render(request, "movies/movie_list.html", {
        "movies": movies
    })


# =========================
# THEATER LIST
# =========================
def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    theaters = Theater.objects.filter(movie=movie)

    return render(request, "movies/theater_list.html", {
        "movie": movie,
        "theaters": theaters
    })


# =========================
# SEAT RESERVATION
# =========================
@login_required(login_url="/login/")
def book_seats(request, theater_id):
    theater = get_object_or_404(Theater, id=theater_id)
    seats = Seat.objects.filter(theater=theater)

    # Auto-release expired reservations
    for seat in seats:
        if seat.is_reserved and seat.is_reservation_expired():
            seat.is_reserved = False
            seat.reserved_at = None
            seat.reserved_by = None
            seat.save()

    if request.method == "POST":
        selected_seats = request.POST.getlist("seats")
        error_seats = []

        if not selected_seats:
            return render(request, "movies/seat_selection.html", {
                "theaters": theater,
                "seats": seats,
                "error": "No seat selected"
            })

        for seat_id in selected_seats:
            seat = get_object_or_404(Seat, id=seat_id, theater=theater)

            if seat.is_booked:
                error_seats.append(seat.seat_number)
                continue

            if seat.is_reserved and seat.reserved_by != request.user:
                error_seats.append(seat.seat_number)
                continue

            seat.is_reserved = True
            seat.reserved_at = timezone.now()
            seat.reserved_by = request.user
            seat.save()

        if error_seats:
            return render(request, "movies/seat_selection.html", {
                "theaters": theater,
                "seats": seats,
                "error": f"Unavailable seats: {', '.join(error_seats)}"
            })

        return redirect("checkout", theater_id=theater.id)

    can_pay = seats.filter(
        is_reserved=True,
        reserved_by=request.user
    ).exists()

    return render(request, "movies/seat_selection.html", {
        "theaters": theater,
        "seats": seats,
        "can_pay": can_pay
    })


# =========================
# STRIPE CHECKOUT
# =========================
@login_required
def create_checkout_session(request, theater_id):
    theater = get_object_or_404(Theater, id=theater_id)

    # Auto-release expired reservations
    all_seats = Seat.objects.filter(theater=theater)
    for seat in all_seats:
        if seat.is_reserved and seat.is_reservation_expired():
            seat.is_reserved = False
            seat.reserved_by = None
            seat.reserved_at = None
            seat.save()

    seats = Seat.objects.filter(
        theater=theater,
        is_reserved=True,
        reserved_by=request.user
    )

    if not seats.exists():
        return redirect("movie_list")

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"Tickets for {theater.movie.name}"
                },
                "unit_amount": 1000,  # $10 per seat
            },
            "quantity": seats.count(),
        }],
        mode="payment",
        success_url=request.build_absolute_uri(
            "/payment-success/"
        ) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=request.build_absolute_uri("/payment-cancel/"),
    )

    return redirect(checkout_session.url)


# =========================
# PAYMENT SUCCESS
# =========================
@login_required
def payment_success(request):
    session_id = request.GET.get("session_id")

    if not session_id:
        return redirect("movie_list")

    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status == "paid":

        seats = Seat.objects.filter(
            is_reserved=True,
            reserved_by=request.user
        )

        if seats.exists() and not Booking.objects.filter(payment_id=session.payment_intent).exists():
            movie_name = seats.first().theater.movie.name
            total_amount = 10 * seats.count()

            for seat in seats:
                Booking.objects.create(
                    user=request.user,
                    seat=seat,
                    movie=seat.theater.movie,
                    theater=seat.theater,
                    is_paid=True,
                    payment_id=session.payment_intent,
                    amount_paid=10
                )

                seat.is_reserved = False
                seat.is_booked = True
                seat.reserved_by = None
                seat.save()

            # Email Confirmation
            if request.user.email:
                send_mail(
                    subject="Booking Confirmation",
                    message=f"Your booking for {movie_name} is confirmed.",
                    from_email=None,
                    recipient_list=[request.user.email],
                    fail_silently=True,
                )

    return render(request, "movies/payment_success.html")


# =========================
# PAYMENT CANCEL
# =========================
@login_required
def payment_cancel(request):
    return render(request, "movies/payment_cancel.html")


# =========================
# ADMIN DASHBOARD
# =========================
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect("movie_list")

    total_revenue = Booking.objects.filter(is_paid=True).aggregate(
        total=Sum("amount_paid")
    )["total"] or 0

    popular_movies = (
        Booking.objects.filter(is_paid=True)
        .values("movie__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    busiest_theaters = (
        Booking.objects.filter(is_paid=True)
        .values("theater__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    return render(request, "movies/admin_dashboard.html", {
        "total_revenue": total_revenue,
        "popular_movies": popular_movies,
        "busiest_theaters": busiest_theaters
    })
