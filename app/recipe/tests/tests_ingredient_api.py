from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTests(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving ingredients"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test the authorized user ingredient APIs"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@hotmail.com',
            'password1234'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving ingredients"""
        Ingredient.objects.create(user=self.user, name="Pepper")
        Ingredient.objects.create(user=self.user, name="Cucumber")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test that ignredients returned are for the authenticated user"""
        user2 = get_user_model().objects.create_user(
            'test2@hotmail.com',
            'sdlfjsdkljf'
        )
        ingredient = Ingredient.objects.create(user=self.user, name="Apple")
        Ingredient.objects.create(user=user2, name="Banana")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test creating a new ingredient"""
        payload = {'name': 'Test ingredient'}
        res = self.client.post(INGREDIENTS_URL, payload)
        exists = Ingredient.objects.filter(
            user=self.user, name=payload['name']).exists()
        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test creating a new ingredient with invalid payload"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        """Test filtering ingredients by those assigned to recipes"""
        ingredient1 = Ingredient.objects.create(
            user=self.user,name='Apples'
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user,name='Turkey'
        )

        recipe = Recipe.objects.create(
            user = self.user,
            title='Apple crumble',
            time_minutes=5,
            price=2.00
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(
            INGREDIENTS_URL,
            {'assigned_only':1}
        )
        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredietns_assigned_unique(self):
        """Test filtering ingredients by assigned returns unique items"""
        ingredient = Ingredient.objects.create(
            user=self.user,name='Eggs'
        )
        Ingredient.objects.create(
            user=self.user,name='Cheese'
        )
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Eggs benedict',
            time_minutes=20,
            price=10.00
        )
        recipe1.ingredients.add(ingredient)

        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Coriander eggs on toast',
            time_minutes=10,
            price=5.00
        )
        recipe2.ingredients.add(ingredient)

        res = self.client.get(
            INGREDIENTS_URL,
            {'assigned_only': 1}
        )

        self.assertEqual(len(res.data),1)