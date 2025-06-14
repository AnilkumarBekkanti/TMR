from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [

  

    # API Endpoints
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('trips/create/', views.trip_create, name='trip_create'),

  

    # # Trips
     path('trips/', views.trip_list, name='trip_list'),             # GET: list all trips
   
    # path('trips/<int:trip_id>/', views.trip_detail, name='trip_detail'),  # GET, PUT, DELETE trip details

    # Itinerary Days
    path('trips/<int:trip_id>/days/', views.itinerary_days_list, name='itinerary_days_list'),
    path('trips/<int:trip_id>/days/<int:day_id>/', views.itinerary_day_detail, name='itinerary_day_detail'),

    # Attractions
    path('days/<int:day_id>/attractions/', views.attraction_list, name='attraction_list'),
    path('days/<int:day_id>/attractions/<int:attraction_id>/', views.attraction_detail, name='attraction_detail'),

    # # Collaborators
    path('trips/<int:trip_id>/collaborators/', views.collaborators_list, name='collaborators_list'),

    # # Travel Tips
    # path('travel-tips/', views.travel_tips_list, name='travel_tips_list'),        # list or add travel tips
    # path('travel-tips/<int:tip_id>/', views.travel_tip_detail, name='travel_tip_detail'),

    # # Shared Links for public/private sharing
    # path('trips/<int:trip_id>/share/', views.generate_share_link, name='generate_share_link'),
    # path('share/<str:token>/', views.access_shared_trip, name='access_shared_trip'),

    # # Expenses (optional)
    # path('trips/<int:trip_id>/expenses/', views.expenses_list, name='expenses_list'),
    # path('trips/<int:trip_id>/expenses/<int:expense_id>/', views.expense_detail, name='expense_detail'),
]
