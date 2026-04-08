import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

# ==========================================
# 1. MULTI-TENANCY: COMPANY MODEL
# ==========================================
class Company(models.Model):
    company_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    subdomain = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# ==========================================
# 2. USER MANAGER
# ==========================================
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

# ==========================================
# 3. CUSTOM USER MODEL
# ==========================================
class User(AbstractBaseUser, PermissionsMixin):
    # User identity
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # NEW: Link user to their specific company!
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees', null=True, blank=True)
    
    email = models.EmailField(unique=True) # Removed editable=False
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    username = models.CharField(max_length=150, unique=True, blank=True)

    # User Residence
    flat_number = models.CharField(max_length=20, blank=True)
    building_name = models.CharField(max_length=100, blank=True) # Lowercased 'b'
    street_name = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)

    # User contact - FIXED IntegerField to CharField
    phone_number = models.CharField(max_length=15, blank=True)
    phone_number2 = models.CharField(max_length=15, blank=True, null=True)

    # User company specific details
    joining_date = models.DateField(blank=True, null=True)  
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Django default fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # last_login is already provided by AbstractBaseUser!

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] # Removed 'username' since we auto-generate it

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email.split('@')[0]  # Default username from email
        super().save(*args, **kwargs)

    def get_roles(self):
        """User ke saare assigned roles ki list return karega"""
        return list(self.user_roles.values_list('role__name', flat=True))

    @property
    def is_tier1(self):
        """CEO, Owner, Admin access check"""
        tier1_roles = ['admin', 'owner', 'ceo']
        return any(role in tier1_roles for role in self.get_roles())

    @property
    def is_manager_plus(self):
        """Manager level and above check"""
        manager_roles = ['manager', 'head']
        return self.is_tier1 or any(role in manager_roles for role in self.get_roles())

    @property
    def highest_role(self):
        """Priority check for multiple roles"""
        roles = self.get_roles()
        # Order of priority
        priority = ['admin', 'owner', 'ceo', 'manager', 'head', 'employee']
        for p in priority:
            if p in roles:
                return p
        return 'employee'

# ==========================================
# 4. ROLES & TEAMS
# ==========================================
class Roles(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('owner', 'Owner'),
        ('ceo', 'CEO'),
        ('manager', 'Manager'),
        ('head', 'Head'),
        ('employee', 'Employee'),
    ]
    role_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=30, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.get_name_display()

class Teams(models.Model):
    TEAM_CHOICES = [
        ('board', 'Board'),
        ('marketing', 'Marketing'),
        ('sales', 'Sales'),
        ('hr', 'HR'),
        ('finance', 'Finance'),
        ('operations', 'Operations'),
        ('it', 'IT'),
        ('customer_support', 'Customer Support'),
    ]
    team_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, choices=TEAM_CHOICES, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.get_name_display()

class UserRoles(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Roles, on_delete=models.CASCADE, related_name="role_users")

    class Meta:
        unique_together = ('user', 'role')
        db_table = 'user_roles'

    def __str__(self):
        return f"{self.user.email} - {self.role.name}"

class UserTeams(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_teams")
    team = models.ForeignKey(Teams, on_delete=models.CASCADE, related_name="team_users")

    class Meta:
        unique_together = ('user', 'team')
        db_table = 'user_teams'

    def __str__(self):
        return f"{self.user.email} - {self.team.name}"