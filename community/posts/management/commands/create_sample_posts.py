from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from posts.models import Post
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create sample posts for testing'

    def handle(self, *args, **options):
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com', 'is_active': True}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created user: {user.username}'))

        # Create sample posts
        posts_data = [
            {
                'title': 'Welcome to Our Community!',
                'content': 'Hello everyone! I\'m excited to be part of this amazing community. This is a great place to share ideas, ask questions, and connect with like-minded people. Feel free to introduce yourself and let us know what you\'re passionate about!'
            },
            {
                'title': 'Best Practices for Web Development',
                'content': 'I wanted to share some best practices I\'ve learned over the years:\n\n1. Always write clean, readable code\n2. Use version control from day one\n3. Test your code thoroughly\n4. Document your work\n5. Stay updated with latest technologies\n\nWhat are your favorite practices? Share in the comments!'
            },
            {
                'title': 'Looking for Collaboration Opportunities',
                'content': 'I\'m a frontend developer with experience in React and Vue.js. Currently looking for interesting projects to collaborate on. If you have a project that needs a dedicated frontend developer, feel free to reach out. Open to both paid and open-source projects!'
            },
            {
                'title': 'Tips for Remote Work Success',
                'content': 'Working remotely has become the new normal. Here are some tips that helped me stay productive:\n\n- Create a dedicated workspace\n- Set clear boundaries between work and personal time\n- Take regular breaks\n- Stay connected with your team\n- Use productivity tools wisely\n\nHow do you manage your remote work routine?'
            },
            {
                'title': 'Introduction to Machine Learning',
                'content': 'Hey everyone! I\'m starting my journey into machine learning and would love to connect with others who are also learning. Currently focusing on Python, TensorFlow, and basic neural networks. If you have resources or tips to share, please drop them below. Let\'s learn together!'
            }
        ]

        for post_data in posts_data:
            post, created = Post.objects.get_or_create(
                title=post_data['title'],
                author=user,
                defaults={'content': post_data['content'], 'author': user}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created post: {post.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'Post {post.title} already exists'))

        self.stdout.write(self.style.SUCCESS('Sample posts created successfully!'))
