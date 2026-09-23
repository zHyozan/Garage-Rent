from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from .models import Space


class LocationTests(APITestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='owner')
        base = dict(owner=self.owner, title='Vaga', description='Vaga segura', price=100, city='São Paulo', state='SP', neighborhood='Centro', address_line='Rua privada', accepted_vehicles=['car'])
        self.near = Space.objects.create(**base, latitude=Decimal('-23.55'), longitude=Decimal('-46.63'))
        self.far = Space.objects.create(**base, latitude=Decimal('-22.90'), longitude=Decimal('-43.20'))
        self.unmapped = Space.objects.create(**base)

    def test_nearby_filters_before_pagination_and_hides_address(self):
        result = self.client.get('/api/spaces/', {'lat': '-23.55', 'lng': '-46.63', 'radius': 5, 'ordering': 'distance'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['count'], 1)
        item = result.data['results'][0]
        self.assertEqual(item['id'], self.near.pk)
        self.assertEqual(item['distance_km'], 0)
        self.assertNotIn('address_line', item)
        self.assertIsNone(item['exact_address'])

    def test_invalid_coordinates_are_400(self):
        for params in [{'lat': 'NaN', 'lng': 0}, {'lat': 91, 'lng': 0}, {'lat': 0}, {'lat': 0, 'lng': 0, 'radius': -1}]:
            self.assertEqual(self.client.get('/api/spaces/', params).status_code, 400)

    def test_unmapped_still_visible_in_regular_search_and_vehicle_filter(self):
        self.assertEqual(self.client.get('/api/spaces/').data['count'], 3)
        self.assertEqual(self.client.get('/api/spaces/', {'vehicle': 'van'}).data['count'], 0)
        self.assertEqual(self.client.get('/api/spaces/', {'vehicle': 'car'}).data['count'], 3)

    def test_coordinates_require_coarse_pair_and_positive_dimensions(self):
        self.client.force_authenticate(self.owner)
        url = f'/api/spaces/{self.near.pk}/'
        for data in [{'latitude': '-23.55123'}, {'latitude': None}, {'length_m': -1}, {'accepted_vehicles': ['aircraft']}, {'accepted_vehicles': ['car', 'car']}]:
            self.assertEqual(self.client.patch(url, data, format='json').status_code, 400)
        self.assertEqual(self.client.patch(url, {'latitude': '', 'longitude': '', 'accepted_vehicles': '["van"]'}, format='multipart').status_code, 200)
        self.near.refresh_from_db()
        self.assertIsNone(self.near.latitude)
        self.assertEqual(self.near.accepted_vehicles, ['van'])
