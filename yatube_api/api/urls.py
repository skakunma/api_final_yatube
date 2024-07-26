from django.urls import path
from .views import PostListCreateAPIView, PostDetailAPIView, CommentListCreateAPIView, CommentDetailAPIView, GroupDetailAPIView
from .views import FollowListCreateAPIView, GroupListCreateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView


urlpatterns = [
    path('v1/posts/', PostListCreateAPIView.as_view(),
         name='post-list-create'),
    path('v1/posts/<int:pk>/', PostDetailAPIView.as_view(),
         name='post-detail'),
    path('v1/posts/<int:post_id>/comments/',
         CommentListCreateAPIView.as_view(), name='comment-list-create'),
    path('v1/posts/<int:post_id>/comments/<int:pk>/',
         CommentDetailAPIView.as_view(), name='comment-detail'),
    path('v1/follow/', FollowListCreateAPIView.as_view(),
         name='follow-list-create'),
    path('v1/groups/', GroupListCreateAPIView.as_view(),
         name='group-list-create'),
    path('v1/groups/<int:pk>/', GroupDetailAPIView.as_view(),
         name='group-detail'),
    path('v1/jwt/create/', TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('v1/jwt/refresh/', TokenRefreshView.as_view(),
         name='token_refresh'),
    path('v1/jwt/verify/', TokenVerifyView.as_view(),
         name='token_verify'),
]
