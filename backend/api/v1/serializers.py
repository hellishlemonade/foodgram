import base64
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from backend.constants import PAGE_SIZE
from favorites.models import FavoritesRecipes
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from shopper.models import ShopRecipes
from subs.models import Subscriber

User = get_user_model()


def _get_user_relation_status(self, obj, relation_field):
    request = self.context.get('request')
    return (
        request and request.user.is_authenticated
        and getattr(obj, relation_field).filter(user=request.user).exists()
    )


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name=f'{uuid.uuid4()}.' + ext)
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


class ProfileSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
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
        return _get_user_relation_status(self, obj, 'subscribers')


class UserWithoutAuthorSerializer(ProfileSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ProfileSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return Subscriber.objects.filter(
            subscriptions=obj, user=user
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit', PAGE_SIZE)
        try:
            limit = int(limit)
        except ValueError:
            pass
        return RecipeShortSerializer(
            Recipe.objects.filter(author=obj)[:limit],
            many=True,
            context={'request': request},
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class SubscriberSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscriber
        fields = ('user', 'subscriptions')
        read_only_fields = ('user', 'subscriptions')

    def validate(self, data):
        request = self.context.get('request')
        subscription_id = (
            self.context.get('request').parser_context.get('kwargs').get('id')
        )
        if request.user.id == int(subscription_id):
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя'
            )
        if Subscriber.objects.filter(
            user_id=request.user.id, subscriptions_id=subscription_id
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на данного пользователя'
            )
        return data

    def to_representation(self, instance):
        return UserWithoutAuthorSerializer(
            instance.subscriptions, context=self.context
        ).data


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
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class WriteRecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = ProfileSerializer()
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='ingredient_links'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        return _get_user_relation_status(self, obj, 'favorites')

    def get_is_in_shopping_cart(self, obj):
        return _get_user_relation_status(self, obj, 'in_shopping_cart')


class CreateRecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = WriteRecipeIngredientSerializer(many=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = ProfileSerializer(read_only=True)

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
        error = {}
        tags = attrs.get('tags', None)
        ingredients = attrs.get('ingredients', None)
        if not tags or not ingredients:
            if not tags:
                error['tags'] = 'Пожалуйста, добавьте теги'
            if not ingredients:
                error['ingredients'] = 'Пожалуйста, добавьте ингредиенты'
            raise ValidationError(error)
        ingredients_dict = attrs.get('ingredients')
        ingredients = [ingredient['id'] for ingredient in ingredients_dict]
        if len(ingredients) != len(set(ingredients)):
            raise ValidationError(
                {'ingredients': 'Ингредиенты не могут дублироваться'}
            )
        tags = attrs.get('tags')
        if len(tags) != len(set(tags)):
            raise ValidationError(
                {'tags': 'Теги не могут дублироваться'}
            )
        return super().validate(attrs)

    def create_tags_and_ingredients(self, tags, ingredients, recipe):
        recipe.tags.set(tags)
        result_ingredients = []
        for ing in ingredients:
            result_ingredients.append(
                RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ing['id'].id,
                    amount=ing['amount']
                )
            )
        RecipeIngredient.objects.bulk_create(result_ingredients)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_tags_and_ingredients(tags, ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.ingredients.clear()
        self.create_tags_and_ingredients(tags, ingredients, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return ReadRecipeSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class FavoritesRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = FavoritesRecipes
        fields = ('user', 'recipes')
        read_only_fields = ('user', 'recipes')

    def validate(self, attrs):
        request = self.context.get('request')
        recipe_id = (
            self.context.get('request').parser_context.get('kwargs').get('id')
        )
        if FavoritesRecipes.objects.filter(
                user_id=request.user.id, recipes_id=recipe_id).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен'
            )
        return attrs

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipes, context=self.context
        ).data


class ShopperRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShopRecipes
        fields = ('user', 'recipes')
        read_only_fields = ('user', 'recipes')

    def validate(self, attrs):
        request = self.context.get('request')
        recipe_id = (
            self.context.get('request').parser_context.get('kwargs').get('id')
        )
        if ShopRecipes.objects.filter(
                user_id=request.user.id, recipes_id=recipe_id).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен'
            )
        return attrs

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipes, context=self.context
        ).data
