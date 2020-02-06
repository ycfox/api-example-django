from django.shortcuts import redirect
from django.views.generic import TemplateView
from social_django.models import UserSocialAuth

from drchrono.endpoints import DoctorEndpoint, AppointmentEndpoint, PatientEndpoint

from pprint import pprint


class SetupView(TemplateView):
    """
    The beginning of the OAuth sign-in flow. Logs a user into the kiosk, and saves the token.
    """
    template_name = 'kiosk_setup.html'


class DoctorWelcome(TemplateView):
    """
    The doctor can see what appointments they have today.
    """
    template_name = 'doctor_welcome.html'

    def get_token(self):
        """
        Social Auth module is configured to store our access tokens. This dark magic will fetch it for us if we've
        already signed in.
        """
        oauth_provider = UserSocialAuth.objects.get(provider='drchrono')
        access_token = oauth_provider.extra_data['access_token']
        return access_token

    def make_api_request(self):
        """
        Use the token we have stored in the DB to make an API request and get doctor details. If this succeeds, we've
        proved that the OAuth setup is working
        """
        # We can create an instance of an endpoint resource class, and use it to fetch details
        access_token = self.get_token()
        api = DoctorEndpoint(access_token)
        # Grab the first doctor from the list; normally this would be the whole practice group, but your hackathon
        # account probably only has one doctor in it.
        return next(api.list())

    def fetch_appointment_list(self):
        """
        Use the token we have stored in the DB to make an API request and get appointment list. 
        """
        # We can create an instance of an endpoint resource class, and use it to fetch details
        access_token = self.get_token()
        api = AppointmentEndpoint(access_token)
        # Grab all appointments from one date
        return api.list(date='2020-02-06')

    def fetch_one_patient(self, id):
        """
        Use the token we have stored in the DB to make an API request and get doctor details. If this succeeds, we've
        proved that the OAuth setup is working
        """
        # We can create an instance of an endpoint resource class, and use it to fetch details
        access_token = self.get_token()
        api = PatientEndpoint(access_token)
        # Fetch one patient.
        return api.fetch(id=id)

    def get_context_data(self, **kwargs):
        kwargs = super(DoctorWelcome, self).get_context_data(**kwargs)
        # Hit the API using one of the endpoints just to prove that we can
        # If this works, then your oAuth setup is working correctly.
        doctor_details = self.make_api_request()
        appointment_list = self.fetch_appointment_list()
        appointments = []
        patients = []
        wait_times = []
        ready_statuses = ['Arrived', 'Checked In', 'Checked In Online']
        for appointment in appointment_list:
            appointments.append(appointment)
            patients.append(self.fetch_one_patient(id=appointment['patient']))
            wait_time = ""
            if appointment['status'] in ready_statuses :
                if hasattr(appointment, 'status_transitions') :
                    transitions = appointment['status_transitions']
                    for trans in transitions:
                        if trans['to_status'] == appointment['status'] :
                            wait_time = trans['datetime']
            wait_times.append(wait_time)
        kwargs['doctor'] = doctor_details
        kwargs['appointments'] = appointments
        kwargs['patients'] = patients
        kwargs['app_details'] = zip(appointments, patients, wait_times)
        return kwargs

