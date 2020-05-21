import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe,Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

# /api/recipe/recipes
# /api/recipe/recipes/1
RECIPES_URL = reverse('recipe:recipe-list')

def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse('recipe:recipe-upload-image',args=[recipe_id])

def detail_url(recipe_id):
    """Return recipe detail url"""
    return reverse('recipe:recipe-detail',args=[recipe_id])

def sample_tag(user,name='Main course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user,name=name)

def sample_ingredient(user,name="Cinamon"):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user,name=name)

def sample_recipe(user,**params):
    """Create and return a sample recipe"""
    defaults = {
        'user' : user,
        'title' :'Sample recipe',
        'time_minutes' : 10,
        'price' : 5.00
    }
    defaults.update(params)

    return Recipe.objects.create(**defaults)

class PublicRecipeApiTests(TestCase):
    """Test unauthenticate recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@hotmail.com'
            'testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL);
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes,many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user"""

        user2 =  get_user_model().objects.create_user(
            'test2@hotmail.com',
            '1234sdjf'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes,many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data),1)
        self.assertEqual(res.data,serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)

    def test_create_basic_recipe(self):
        """Test creating a basic recipe"""
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': 5.00
        }

        res = self.client.post(RECIPES_URL,payload)

        self.assertEqual(res.status_code , status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            #getattr function retrieves the attribute from an object based
            #on the provided key , it is like recipe[key] in javascript
            #but in python object is different in comparison to dictionary
            self.assertEqual(payload[key],getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        tag1 = sample_tag(user=self.user,name='Vegan')
        tag2 = sample_tag(user=self.user,name='Dessert')
        payload = {
            'title':'Avocado lime cheesecake',
            'tags' : [tag1.id, tag2.id],
            'time_minutes': 60,
            'price' : 20.00
        }
        res = self.client.post(RECIPES_URL,payload)

        self.assertEqual(res.status_code,status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(),2)
        #assert in can be used for lists and querysets to chech membership of items
        self.assertIn(tag1,tags)
        self.assertIn(tag2,tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating recipe with ingredients"""
        ingredient11 = sample_ingredient(user=self.user,name="Prawns")
        ingredient12 = sample_ingredient(user=self.user,name="Ginger")
        payload = {
            'title' : 'Thai prawn red curry',
            'ingredients' : [ingredient11.id, ingredient12.id],
            'time_minutes': 30,
            'price': 10.00
        }
        res = self.client.post(RECIPES_URL,payload)

        self.assertEqual(res.status_code,status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(),2)
        self.assertIn(ingredient11,ingredients)
        self.assertIn(ingredient12,ingredients)


    def test_recipe_partial_update(self):
        """Test updating a recipe with PATCH"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user,name='Curry')

        payload = {
            'title': 'Chicke tikka',
            'tags': [new_tag.id]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url,payload)
        #refresh the object details since it is updated through rest api client
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags),1)
        self.assertIn(new_tag,tags)



    def test_recipe_full_update(self):
        """Test updating a recipe with PUT"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {
            'title' : 'Spaghetti carbonara',
            'time_minutes' : 20,
            'price': 5.00
        }
        url = detail_url(recipe.id)
        res = self.client.put(url,payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title,payload['title'])
        self.assertEqual(recipe.time_minutes,payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(recipe.tags.all().count(),0)


    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""
        recipe1 = sample_recipe(user=self.user,title='Thai vegetable curry')
        recipe2 = sample_recipe(user=self.user,title='Aubergine with tahini')
        tag1 = sample_tag(user=self.user,name='Vegan')
        tag2 = sample_tag(user=self.user,name='Vegetarian')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=self.user, title='Fish and chips')

        res = self.client.get(
            RECIPES_URL,
            {'tags': f'{tag1.id},{tag2.id}'}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data , res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """Test returning recipes with specifice ingredients"""
        recipe1 = sample_recipe(user=self.user,title='Posh beans on toast')
        recipe2 = sample_recipe(user=self.user,title='Chicken cacciatore')
        ingredient1 = sample_ingredient(user=self.user, name='Feta Cheese')
        ingredient2 = sample_ingredient(user=self.user,name='Chicken')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user = self.user, title='Steak and mushroom')

        res = self.client.get(
            RECIPES_URL,
            {'ingredients':f'{ingredient1.id},{ingredient2.id}'}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
 

class RecipeImageUploadTests(TestCase):


    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@hotmail.com',
            '12345sdf'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)


    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading an image to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB',(10,10)) #creates a black square 10 x 10 pixels
            img.save(ntf,format='JPEG')
            ntf.seek(0)
            res = self.client.post(url,{'image':ntf},fomrat='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code , status.HTTP_200_OK)
        self.assertIn('image',res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url,{'image':'notImage'},format='multipart')

        self.assertEqual(res.status_code,status.HTTP_400_BAD_REQUEST)