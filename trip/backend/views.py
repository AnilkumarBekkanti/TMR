from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .models import User, Trip, ItineraryDay, Attraction, TripCollaborator
import json
from datetime import datetime

@csrf_exempt
def register(request):
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        response = JsonResponse({'message': 'CORS preflight successful'}, status=200)
        response["Access-Control-Allow-Origin"] = "http://127.0.0.1:5500"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        response["Access-Control-Allow-Credentials"] = "true"
        return response

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            phone_number = data.get('phone_number')
            password = data.get('password')

            errors = {}
            if not first_name:
                errors['first_name'] = 'First name is required'
            if not last_name:
                errors['last_name'] = 'Last name is required'
            if not email:
                errors['email'] = 'Email is required'
            if not password:
                errors['password'] = 'Password is required'

            if errors:
                response = JsonResponse({'success': False, 'errors': errors}, status=400)
                response["Access-Control-Allow-Origin"] = "http://127.0.0.1:5500"
                response["Access-Control-Allow-Credentials"] = "true"
                return response

            if User.objects.filter(email=email).exists():
                response = JsonResponse({'success': False, 'errors': {'email': 'Email already registered'}}, status=400)
                response["Access-Control-Allow-Origin"] = "http://127.0.0.1:5500"
                response["Access-Control-Allow-Credentials"] = "true"
                return response

            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                password_hash=make_password(password)
            )

            response = JsonResponse({'success': True, 'message': 'User registered successfully'}, status=201)
            response["Access-Control-Allow-Origin"] = "http://127.0.0.1:5500"
            response["Access-Control-Allow-Credentials"] = "true"
            return response

        except json.JSONDecodeError:
            response = JsonResponse({'success': False, 'errors': {'general': 'Invalid JSON data'}}, status=400)
            response["Access-Control-Allow-Origin"] = "http://127.0.0.1:5500"
            response["Access-Control-Allow-Credentials"] = "true"
            return response
        except Exception as e:
            response = JsonResponse({'success': False, 'errors': {'general': str(e)}}, status=500)
            response["Access-Control-Allow-Origin"] = "http://127.0.0.1:5500"
            response["Access-Control-Allow-Credentials"] = "true"
            return response

    # If not POST or OPTIONS
    response = JsonResponse({'success': False, 'errors': {'general': 'Only POST method allowed'}}, status=405)
    response["Access-Control-Allow-Origin"] = "http://127.0.0.1:5500"
    response["Access-Control-Allow-Credentials"] = "true"
    return response



@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            # Validate required fields
            errors = {}
            if not email:
                errors['email'] = 'Email is required'
            if not password:
                errors['password'] = 'Password is required'

            if errors:
                return JsonResponse({
                    'success': False,
                    'errors': errors
                }, status=400)

            try:
                user = User.objects.get(email=email)
                if check_password(password, user.password_hash):
                    response = JsonResponse({
                        'success': True,
                        'message': 'Login successful',
                        'user_id': user.id,
                        'name': f"{user.first_name} {user.last_name}"
                    })
                    response["Access-Control-Allow-Origin"] = "http://127.0.0.1:5500"
                    response["Access-Control-Allow-Credentials"] = "true"
                    return response
                else:
                    return JsonResponse({
                        'success': False,
                        'errors': {'password': 'Invalid password'}
                    }, status=401)

            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'errors': {'email': 'User not found'}
                }, status=404)

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'errors': {'general': 'Invalid JSON data'}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': {'general': str(e)}
            }, status=500)

    return JsonResponse({
        'success': False,
        'errors': {'general': 'Only POST method allowed'}
    }, status=405)

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Trip, User
from datetime import datetime


@csrf_exempt
def trip_create(request):
    if request.method == 'POST':
        try:
            # 1. Get user ID from custom request header
            user_id = request.headers.get('X-User-ID')

            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            # 2. Fetch user from the database
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

            # 3. Parse JSON data from request body
            data = json.loads(request.body)

            # 4. Extract and validate required fields
            trip_name = data.get('trip_name')
            destination = data.get('destination')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            is_public = data.get('is_public', False)
            description = data.get('description', '')

            if not all([trip_name, destination, start_date, end_date]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # 5. Convert date strings to date objects
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

            # 6. Create the Trip instance
            trip = Trip.objects.create(
                user=user,
                trip_name=trip_name,
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                is_public=is_public,
                description=description
            )

            # 7. Return the response
            response = JsonResponse({
                'message': 'Trip created successfully',
                'trip': {
                    'id': trip.id,
                    'trip_name': trip.trip_name,
                    'destination': trip.destination,
                    'start_date': trip.start_date.strftime('%Y-%m-%d'),
                    'end_date': trip.end_date.strftime('%Y-%m-%d'),
                    'is_public': trip.is_public,
                    'description': trip.description,
                    'created_at': trip.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(trip, 'created_at') else ''
                }
            }, status=201)

            # 8. CORS headers (if called from browser/JS app)
            response["Access-Control-Allow-Origin"] = "http://127.0.0.1:5500"
            response["Access-Control-Allow-Credentials"] = "true"
            return response

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Only POST method allowed'}, status=405)

@csrf_exempt
def trip_list(request):
    if request.method == 'GET':
        try:
            user_id = request.headers.get('X-User-ID')
            
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)
                
            user = User.objects.get(id=user_id)
            
            # Get all trips for the user
            trips = Trip.objects.filter(user=user).order_by('-created_at')
            
            # Convert trips to list of dictionaries
            trips_data = []
            for trip in trips:
                trip_data = {
                    'id': trip.id,
                    'trip_name': trip.trip_name,
                    'destination': trip.destination,
                    'start_date': trip.start_date.strftime('%Y-%m-%d'),
                    'end_date': trip.end_date.strftime('%Y-%m-%d'),
                    'is_public': trip.is_public,
                    'description': trip.description,
                    'created_at': trip.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'upcoming' if trip.start_date > datetime.now().date() else 'active' if trip.start_date <= datetime.now().date() <= trip.end_date else 'completed'
                }
                trips_data.append(trip_data)
            
            response = JsonResponse({'trips': trips_data})
            response["Access-Control-Allow-Origin"] = "http://127.0.0.1:5500"
            response["Access-Control-Allow-Credentials"] = "true"
            return response
            
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Only GET method allowed'}, status=405)

@csrf_exempt
def itinerary_days_list(request, trip_id):
    if request.method == 'GET':
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            trip = Trip.objects.get(id=trip_id)
            # Check if user is trip owner or collaborator
            if trip.user_id != int(user_id) and not TripCollaborator.objects.filter(trip=trip, user_id=user_id).exists():
                return JsonResponse({'error': 'Unauthorized access'}, status=403)

            days = ItineraryDay.objects.filter(trip=trip).order_by('day_number')
            days_data = []
            for day in days:
                attractions = Attraction.objects.filter(itinerary_day=day)
                attractions_data = [{
                    'id': attr.id,
                    'name': attr.name,
                    'location': attr.location,
                    'description': attr.description,
                    'time_slot': attr.time_slot,
                    'map_url': attr.map_url
                } for attr in attractions]
                
                days_data.append({
                    'id': day.id,
                    'day_number': day.day_number,
                    'date': day.date.strftime('%Y-%m-%d'),
                    'notes': day.notes,
                    'attractions': attractions_data
                })

            return JsonResponse({'days': days_data})

        except Trip.DoesNotExist:
            return JsonResponse({'error': 'Trip not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'POST':
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            trip = Trip.objects.get(id=trip_id)
            # Check if user is trip owner or collaborator with edit permissions
            if trip.user_id != int(user_id) and not TripCollaborator.objects.filter(trip=trip, user_id=user_id, can_edit=True).exists():
                return JsonResponse({'error': 'Unauthorized access'}, status=403)

            data = json.loads(request.body)
            day_number = data.get('day_number')
            date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
            notes = data.get('notes', '')

            day = ItineraryDay.objects.create(
                trip=trip,
                day_number=day_number,
                date=date,
                notes=notes
            )

            return JsonResponse({
                'id': day.id,
                'day_number': day.day_number,
                'date': day.date.strftime('%Y-%m-%d'),
                'notes': day.notes
            }, status=201)

        except Trip.DoesNotExist:
            return JsonResponse({'error': 'Trip not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def itinerary_day_detail(request, trip_id, day_id):
    if request.method == 'GET':
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            trip = Trip.objects.get(id=trip_id)
            if trip.user_id != int(user_id) and not TripCollaborator.objects.filter(trip=trip, user_id=user_id).exists():
                return JsonResponse({'error': 'Unauthorized access'}, status=403)

            day = ItineraryDay.objects.get(id=day_id, trip=trip)
            attractions = Attraction.objects.filter(itinerary_day=day)
            attractions_data = [{
                'id': attr.id,
                'name': attr.name,
                'location': attr.location,
                'description': attr.description,
                'time_slot': attr.time_slot,
                'map_url': attr.map_url
            } for attr in attractions]

            return JsonResponse({
                'id': day.id,
                'day_number': day.day_number,
                'date': day.date.strftime('%Y-%m-%d'),
                'notes': day.notes,
                'attractions': attractions_data
            })

        except (Trip.DoesNotExist, ItineraryDay.DoesNotExist):
            return JsonResponse({'error': 'Not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'PUT':
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            trip = Trip.objects.get(id=trip_id)
            if trip.user_id != int(user_id) and not TripCollaborator.objects.filter(trip=trip, user_id=user_id, can_edit=True).exists():
                return JsonResponse({'error': 'Unauthorized access'}, status=403)

            day = ItineraryDay.objects.get(id=day_id, trip=trip)
            data = json.loads(request.body)

            if 'day_number' in data:
                day.day_number = data['day_number']
            if 'date' in data:
                day.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            if 'notes' in data:
                day.notes = data['notes']

            day.save()

            return JsonResponse({
                'id': day.id,
                'day_number': day.day_number,
                'date': day.date.strftime('%Y-%m-%d'),
                'notes': day.notes
            })

        except (Trip.DoesNotExist, ItineraryDay.DoesNotExist):
            return JsonResponse({'error': 'Not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            trip = Trip.objects.get(id=trip_id)
            if trip.user_id != int(user_id) and not TripCollaborator.objects.filter(trip=trip, user_id=user_id, can_edit=True).exists():
                return JsonResponse({'error': 'Unauthorized access'}, status=403)

            day = ItineraryDay.objects.get(id=day_id, trip=trip)
            day.delete()

            return JsonResponse({'message': 'Day deleted successfully'})

        except (Trip.DoesNotExist, ItineraryDay.DoesNotExist):
            return JsonResponse({'error': 'Not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def attraction_list(request, day_id):
    if request.method == 'GET':
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            day = ItineraryDay.objects.get(id=day_id)
            trip = day.trip
            if trip.user_id != int(user_id) and not TripCollaborator.objects.filter(trip=trip, user_id=user_id).exists():
                return JsonResponse({'error': 'Unauthorized access'}, status=403)

            attractions = Attraction.objects.filter(itinerary_day=day)
            attractions_data = [{
                'id': attr.id,
                'name': attr.name,
                'location': attr.location,
                'description': attr.description,
                'time_slot': attr.time_slot,
                'map_url': attr.map_url
            } for attr in attractions]

            return JsonResponse({'attractions': attractions_data})

        except ItineraryDay.DoesNotExist:
            return JsonResponse({'error': 'Day not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'POST':
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            day = ItineraryDay.objects.get(id=day_id)
            trip = day.trip
            if trip.user_id != int(user_id) and not TripCollaborator.objects.filter(trip=trip, user_id=user_id, can_edit=True).exists():
                return JsonResponse({'error': 'Unauthorized access'}, status=403)

            data = json.loads(request.body)
            attraction = Attraction.objects.create(
                itinerary_day=day,
                name=data['name'],
                location=data['location'],
                description=data.get('description', ''),
                time_slot=data.get('time_slot', ''),
                map_url=data.get('map_url', '')
            )

            return JsonResponse({
                'id': attraction.id,
                'name': attraction.name,
                'location': attraction.location,
                'description': attraction.description,
                'time_slot': attraction.time_slot,
                'map_url': attraction.map_url
            }, status=201)

        except ItineraryDay.DoesNotExist:
            return JsonResponse({'error': 'Day not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def attraction_detail(request, day_id, attraction_id):
    if request.method == 'GET':
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            day = ItineraryDay.objects.get(id=day_id)
            trip = day.trip
            if trip.user_id != int(user_id) and not TripCollaborator.objects.filter(trip=trip, user_id=user_id).exists():
                return JsonResponse({'error': 'Unauthorized access'}, status=403)

            attraction = Attraction.objects.get(id=attraction_id, itinerary_day=day)
            return JsonResponse({
                'id': attraction.id,
                'name': attraction.name,
                'location': attraction.location,
                'description': attraction.description,
                'time_slot': attraction.time_slot,
                'map_url': attraction.map_url
            })

        except (ItineraryDay.DoesNotExist, Attraction.DoesNotExist):
            return JsonResponse({'error': 'Not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'PUT':
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            day = ItineraryDay.objects.get(id=day_id)
            trip = day.trip
            if trip.user_id != int(user_id) and not TripCollaborator.objects.filter(trip=trip, user_id=user_id, can_edit=True).exists():
                return JsonResponse({'error': 'Unauthorized access'}, status=403)

            attraction = Attraction.objects.get(id=attraction_id, itinerary_day=day)
            data = json.loads(request.body)

            if 'name' in data:
                attraction.name = data['name']
            if 'location' in data:
                attraction.location = data['location']
            if 'description' in data:
                attraction.description = data['description']
            if 'time_slot' in data:
                attraction.time_slot = data['time_slot']
            if 'map_url' in data:
                attraction.map_url = data['map_url']

            attraction.save()

            return JsonResponse({
                'id': attraction.id,
                'name': attraction.name,
                'location': attraction.location,
                'description': attraction.description,
                'time_slot': attraction.time_slot,
                'map_url': attraction.map_url
            })

        except (ItineraryDay.DoesNotExist, Attraction.DoesNotExist):
            return JsonResponse({'error': 'Not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            day = ItineraryDay.objects.get(id=day_id)
            trip = day.trip
            if trip.user_id != int(user_id) and not TripCollaborator.objects.filter(trip=trip, user_id=user_id, can_edit=True).exists():
                return JsonResponse({'error': 'Unauthorized access'}, status=403)

            attraction = Attraction.objects.get(id=attraction_id, itinerary_day=day)
            attraction.delete()

            return JsonResponse({'message': 'Attraction deleted successfully'})

        except (ItineraryDay.DoesNotExist, Attraction.DoesNotExist):
            return JsonResponse({'error': 'Not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)





@csrf_exempt
def collaborators_list(request, trip_id):
    if request.method == 'GET':
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            trip = Trip.objects.get(id=trip_id)
            if trip.user_id != int(user_id) and not TripCollaborator.objects.filter(trip=trip, user_id=user_id).exists():
                return JsonResponse({'error': 'Unauthorized access'}, status=403)

            collaborators = TripCollaborator.objects.filter(trip=trip).select_related('user')
            collaborators_data = [{
                'id': collab.id,
                'user': {
                    'id': collab.user.id,
                    'first_name': collab.user.first_name,
                    'last_name': collab.user.last_name,
                    'email': collab.user.email
                },
                'can_edit': collab.can_edit
            } for collab in collaborators]

            return JsonResponse({'collaborators': collaborators_data})

        except Trip.DoesNotExist:
            return JsonResponse({'error': 'Trip not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'POST':
        try:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)

            trip = Trip.objects.get(id=trip_id)
            if trip.user_id != int(user_id):
                return JsonResponse({'error': 'Only trip owner can add collaborators'}, status=403)

            data = json.loads(request.body)
            collaborator_email = data.get('email')
            can_edit = data.get('can_edit', False)

            try:
                collaborator_user = User.objects.get(email=collaborator_email)
                if collaborator_user.id == int(user_id):
                    return JsonResponse({'error': 'Cannot add yourself as a collaborator'}, status=400)

                if TripCollaborator.objects.filter(trip=trip, user=collaborator_user).exists():
                    return JsonResponse({'error': 'User is already a collaborator'}, status=400)

                collaborator = TripCollaborator.objects.create(
                    trip=trip,
                    user=collaborator_user,
                    can_edit=can_edit
                )

                return JsonResponse({
                    'id': collaborator.id,
                    'user': {
                        'id': collaborator.user.id,
                        'first_name': collaborator.user.first_name,
                        'last_name': collaborator.user.last_name,
                        'email': collaborator.user.email
                    },
                    'can_edit': collaborator.can_edit
                }, status=201)

            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

        except Trip.DoesNotExist:
            return JsonResponse({'error': 'Trip not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
