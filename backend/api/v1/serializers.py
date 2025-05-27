import base64
import uuid

from djoser.serializers import UserCreateSerializer
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from subs.models import Subscriber
from recipes.models import Tag, Recipe, Ingredient, RecipeIngredient
from favorites.models import FavoritesRecipes
from shopper.models import ShopRecipes


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name=f'{uuid.uuid4()}.' + ext)
            print(data)
        return super().to_internal_value(data)


class ImageSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class MyUserCreateSerializer(UserCreateSerializer):

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class MyUserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            subscriber = Subscriber.objects.filter(user=request.user).first()
            if subscriber:
                return subscriber.subscriptions.filter(id=obj.id).exists()
        return False


class UserWithoutAuthorSerializer(MyUserSerializer):

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = Recipe.objects.filter(
                author=obj).order_by('-id')[:int(limit)]
            serializer = RecipeShortSerializer(recipes, many=True)
            return serializer.data
        recipes = Recipe.objects.filter(author=obj)
        serializer = RecipeShortSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        recipes = Recipe.objects.filter(author=obj).count()
        return recipes


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = ('name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class TagField(serializers.RelatedField):

    def to_internal_value(self, data):
        try:
            get_object_or_404(Tag, id=data)
        except Exception as e:
            raise ValidationError(e)
        return data

    def to_representation(self, value):
        return {'id': value.id, 'name': value.name, 'slug': value.slug}


class IngredientField(serializers.RelatedField):

    def to_internal_value(self, data):
        try:
            get_object_or_404(Ingredient, id=data['id'])
        except Exception as e:
            raise ValidationError(e)
        return data

    def to_representation(self, value):
        return {
            'id': value.id,
            'name': value.name,
            'measurement_unit': value.measurement_unit
        }


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagField(queryset=Tag.objects.all(), many=True)
    ingredients = IngredientField(queryset=Ingredient.objects.all(), many=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = MyUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )
        read_only_fields = ('author',)

    def validate(self, attrs):
        error_message = 'Ожидается непустой список'
        error = {}
        tags = attrs.get('tags', None)
        ingredients = attrs.get('ingredients', None)
        if not tags or not ingredients:
            if not tags:
                error['tags'] = error_message
            if not ingredients:
                error['ingredients'] = error_message
            raise ValidationError(error)
        error_message = 'Не могут дублироваться'
        ingredients_dict = attrs.get('ingredients')
        ingredients = [ingredient['id'] for ingredient in ingredients_dict]
        if len(ingredients) != len(set(ingredients)):
            raise ValidationError(
                {'ingredients': error_message}
            )
        tags = attrs.get('tags')
        if len(tags) != len(set(tags)):
            raise ValidationError(
                {'tags': error_message}
            )
        return super().validate(attrs)

    def validate_ingredients(self, value):
        serializer = RecipeIngredientSerializer(data=value, many=True)
        serializer.is_valid(raise_exception=True)
        return serializer.data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ing in ingredients:
            ingredient = Ingredient.objects.get(id=ing['id'])
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=ingredient, amount=ing['amount'])
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.clear()
            instance.tags.set(tags)
        if ingredients is not None:
            instance.ingredients.clear()
            for ing in ingredients:
                ingredient = get_object_or_404(Ingredient, id=ing['id'])
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=ing['amount']
                )
        return instance

    def to_representation(self, instance):
        recipe_ingredients = RecipeIngredient.objects.filter(
            recipe=instance
        ).select_related('ingredient')
        recipe = super().to_representation(instance)
        recipe['ingredients'] = [
            {
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                'measurement_unit': ri.ingredient.measurement_unit,
                'amount': ri.amount
            }
            for ri in recipe_ingredients
        ]
        return recipe

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoritesRecipes.objects.filter(
                user=request.user, recipes=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShopRecipes.objects.filter(
                user=request.user, recipes=obj).exists()
        return False
