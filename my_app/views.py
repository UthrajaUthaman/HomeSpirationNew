import json
from django.shortcuts import redirect, render
from .models import NormalUser, ProfessionalDetails, User ,Professional
from django.contrib import messages
from django.contrib.auth import authenticate ,login,logout, get_user_model
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import make_password
from .models import Professional
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist


# Create your views here.
def index(request):
    return render(request,'index.html')

def professional_dashboard(request):
    professional = None
    if hasattr(request.user, 'professional'):
        professional = request.user.professional
    return render(request, 'professional_home.html', {'professional': professional})

#def login(request):
#    return render(request,'login.html')

def signup(request):
    return render(request,'signup.html')

#def signuppro(request):
#    return render(request,'professional_signup.html')

def about(request):
    return render(request,'about.html')


def register_normal_user(request):

    error_messages = {}
    if request.method == 'POST':
        fname = request.POST['fname']
        lname = request.POST['lname']
        uname = request.POST['uname']
        email = request.POST['email']
        phone = request.POST['phone']
        password = request.POST['pass']
        cpassword = request.POST['cpass']

        if User.objects.filter(username=uname).exists():
            error_messages['uname'] = 'Username already taken'  
        if User.objects.filter(email=email).exists():
            error_messages['email'] = 'Email already taken'  

        if not error_messages:
            user = User(username=uname, email=email, is_user=True)
            user.set_password(password)
            user.save()

            normal_user = NormalUser(user=user, first_name=fname, last_name=lname, phone_number=phone)
            normal_user.save()

            return redirect('login')

    return render(request, 'signup.html')


def register_professional(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        company_name = request.POST.get('company_name')
        phone_number = request.POST.get('phone_number')
        country = request.POST.get('country')
        state = request.POST.get('state')
        city = request.POST.get('city')
        pincode = request.POST.get('pincode')
        license_number = request.POST.get('license_number')
        # Assuming you're handling file uploads with Django's default storage system
        license_document = request.FILES.get('license_document')

        print(username, email, password, company_name, phone_number, country, state, city, pincode, license_number,license_document)

        # Basic validation
        if not all([username, email, password, company_name, phone_number, country, state, city, pincode, license_number, license_document]):
            return HttpResponse("All fields are required.", status=400)
        
        if User.objects.filter(username=username).exists():
            return HttpResponse("Username already taken.", status=400)
        
        if User.objects.filter(email=email).exists():
            return HttpResponse("Email already exists.", status=400)
        
        # Create User
        user = User(username=username, email=email ,is_professional=True)
        user.set_password(password)# Hash the password
        user.save()

        # Save license_document
        fs = FileSystemStorage()
        filename = fs.save(license_document.name, license_document)
        uploaded_file_url = fs.url(filename)
        
        # Create Professional
        professional = Professional(
            user=user,
            company_name=company_name,
            phone_number=phone_number,
            country=country,
            state=state,
            city=city,
            pincode=pincode,
            license_document=uploaded_file_url,
            license_number=license_number,
            company_verified=False 
        )
        professional.save()

        return redirect('login')  
    else:
        return render(request, 'professional_signup.html')



def loginnew(request):
    if request.method == 'POST':
        username = request.POST['uname']
        password = request.POST['pass']
        
        user = authenticate(request, username=username, password=password)
        print(user)
        
        if user is not None:
            login(request, user)
            if user.is_user:
                messages.success(request, 'You successfully signed in as a normal user.')
                return redirect('index')
            elif user.is_professional:
                try:
                    professional = Professional.objects.get(user=user)
                    if professional.company_verified:
                        login(request, user)
                        return redirect('professional_dashboard')
                    else:
                        messages.error(request, 'Your company has not been verified yet.')
                        return redirect('login')
                except Professional.DoesNotExist:
                    messages.error(request, 'Professional profile not found.')
                    return redirect('login')
            elif user.is_superuser:
                return redirect('admin_home')
        else:
            return render(request, 'login.html', {'error_message': 'Username or password is incorrect'})
            

    return render(request, 'login.html')

@login_required
@require_POST
def submit_professional_type_services(request):
    user = request.user
    company_type = request.POST.getlist('company_type')
    services_offered = request.POST.getlist('services_offered')
    try:
        professional, created = Professional.objects.get_or_create(user=user)
        professional.company_type = company_type[0] if company_type else ''
        professional.save()
        professional_details, created = ProfessionalDetails.objects.get_or_create(professional=professional)
        professional_details.services_offered = services_offered[0] if company_type else ''
        professional_details.save()
        # Successfully saved, instruct the client to open the next modal
        return JsonResponse({"success": True, "nextModal": "modal2"}, status=200)
    except Exception as e:
        # Error handling
        return JsonResponse({"success": False, "error": str(e)}, status=400)

@login_required
@require_POST
def submit_professional_website_info(request):
    user = request.user
    website_link = request.POST.get('website_link')
    professional_info = request.POST.get('professional_info')
    business_description = request.POST.get('business_description')
    certifications = request.POST.get('certifications')

    try:
        professional = Professional.objects.get(user=user)
        professional_details, created = ProfessionalDetails.objects.get_or_create(professional=professional)
        professional_details.website_link = website_link
        professional_details.professional_information = professional_info
        professional_details.business_description = business_description
        professional_details.certifications_and_awards = certifications
        professional_details.save()
        # Successfully saved, instruct the client to open the next modal
        return JsonResponse({"success": True, "nextModal": "modal3"}, status=200)
    except Exception as e:
        # Error handling
        return JsonResponse({"success": False, "error": str(e)}, status=400)

@login_required
@require_POST
def submit_professional_final_details(request):
    user = request.user
    typical_job_cost = request.POST.get('typical_job_cost')
    number_of_projects = request.POST.get('number_of_projects')
    profile_picture = request.FILES.get('profile_picture')
    cover_photo = request.FILES.get('cover_photo')

    try:
        professional, created = Professional.objects.get_or_create(user=user)

        fs = FileSystemStorage()
        filename = fs.save(profile_picture.name, profile_picture)
        uploaded_profile_picture = fs.url(filename)

        fs = FileSystemStorage()
        filenamee = fs.save(cover_photo.name, cover_photo)
        uploaded_cover_photo = fs.url(filenamee)

        professional.profile_photo = uploaded_profile_picture
        professional.cover_photo = uploaded_cover_photo
        professional.save()
        professional_details = ProfessionalDetails.objects.get(professional=professional)
        professional_details.typical_job_cost = typical_job_cost
        professional_details.number_of_projects = number_of_projects
        professional_details.save()
        # Final step completed, you can instruct the client to redirect or display a success message
        return JsonResponse({"success": True, "message": "Final details submitted successfully!"}, status=200)
    except Exception as e:
        # Error handling
        return JsonResponse({"success": False, "error": str(e)}, status=400)

def logoutp(request):
    logout(request)
    return redirect('login')