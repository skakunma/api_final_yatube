from rest_framework import generics
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework import status
from django_filters import FilterSet, CharFilter
from .permissions import IsAuthenticatedOrReadOnly
from posts.models import Post, Comment, Follow, Group, User
from .serializers import (PostSerializer, CommentSerializer,
                          FollowSerializer, GroupSerializer)
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from .pagination import PostPagination, CommentPagination
from rest_framework import serializers
from rest_framework import filters


class FollowFilter(FilterSet):
    search = CharFilter(field_name='following__username',
                        lookup_expr='icontains')

    class Meta:
        model = Follow
        fields = ['search']


class PostListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PostPagination

    def get_queryset(self):
        return Post.objects.all().order_by('pub_date')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if ('limit' not in request.query_params
                and 'offset' not in request.query_params):
            serializer = self.get_serializer(queryset, many=True)

            return Response(serializer.data)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PostPagination

    def get_queryset(self):
        return Post.objects.all()

    def perform_update(self, serializer):
        post = self.get_object()
        if post.author != self.request.user:
            raise PermissionDenied('Вы не можете изменить этот пост.')
        serializer.save()

    def delete(self, request, *args, **kwargs):
        post = self.get_object()

        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if post.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(post)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, *args, **kwargs):
        post = self.get_object()

        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if post.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        post = self.get_object()

        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if post.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CommentPagination

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id).order_by('created')

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied(
                "Authentication credentials were not provided.")
        serializer.save(author=self.request.user,
                        post_id=self.kwargs['post_id'])

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CommentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id)

    def perform_update(self, serializer):
        comment = self.get_object()
        if comment.author != self.request.user:
            raise PermissionDenied('У вас нет прав оставить комет.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied('У вас нет прав удалить комет.')
        super().perform_destroy(instance)


class FollowListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = FollowFilter
    search_fields = ('following__username',)

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user).order_by('user')

    def perform_create(self, serializer):
        following_username = self.request.data.get('following')
        if following_username == self.request.user.username:
            raise serializers.ValidationError("You cannot follow yourself.")

        user_to_follow = User.objects.filter(
            username=following_username).first()

        if user_to_follow is None:
            raise serializers.ValidationError("User to follow does not exist.")

        if Follow.objects.filter(user=self.request.user,
                                 following=user_to_follow).exists():
            raise serializers.ValidationError(
                "You are already following this user.")

        serializer.save(user=self.request.user, following=user_to_follow)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GroupListCreateAPIView(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Group.objects.all()

    def post(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class GroupDetailAPIView(generics.RetrieveAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    lookup_field = 'pk'
