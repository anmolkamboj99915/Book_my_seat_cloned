from django.urls import path
from . import views

urlpatterns = [

    # Movie listing + filters
    path('', views.movie_list, name='movie_list'),

    # Theater listing for a movie
    path('<int:movie_id>/theaters/', views.theater_list, name='theater_list'),

    # Seat selection + reservation
    path('theater/<int:theater_id>/seats/book/', views.book_seats, name='book_seats'),

    # Stripe Checkout
    path('checkout/<int:theater_id>/', views.create_checkout_session, name='checkout'),

    # Payment result pages
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),

    # Admin Analytics Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
