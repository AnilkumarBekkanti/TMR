from django.db import models

class User(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users'

class Trip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trip_name = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    is_public = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trips'

class ItineraryDay(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    day_number = models.IntegerField()
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'itinerary_days'

class Attraction(models.Model):
    itinerary_day = models.ForeignKey(ItineraryDay, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    time_slot = models.CharField(max_length=100, blank=True, null=True)
    map_url = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'attractions'

class Expense(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    
    class Meta:
        db_table = 'expenses'

class TripCollaborator(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    can_edit = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'trip_collaborators'
        unique_together = ('trip', 'user')

class TripNote(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trip_notes'

class TripGallery(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    image_path = models.CharField(max_length=255)
    caption = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trip_gallery'

class TravelTip(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'travel_tips'

class WeatherForecast(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    date = models.DateField()
    forecast = models.CharField(max_length=255, blank=True, null=True)
    temperature = models.FloatField(blank=True, null=True)
    
    class Meta:
        db_table = 'weather_forecast'