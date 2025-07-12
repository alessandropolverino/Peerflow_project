<script setup lang="ts">
import { ref } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

const router = useRouter();
const config = useRuntimeConfig();
// @ts-ignore
const AUTH_API_URL = config.public.authApiUrl;

const name = ref('');
const surname = ref('');
const email = ref('');
const role = ref('');
const password = ref('');

function clearForm() {
    name.value = '';
    surname.value = '';
    email.value = '';
    role.value = '';
    password.value = '';
}

function signUp() {
   
    if (!name.value || !surname.value || !email.value || !role.value || !password.value) {
        alert('Please fill in all fields.');
        return;
    }

    const userData = {
        name: name.value,
        surname: surname.value,
        email: email.value,
        role: role.value,
        password: password.value
    };

    axios.post(AUTH_API_URL+'/authentication/signup', userData)
        .then(response => {
            console.log(AUTH_API_URL+'/authentication/signup');
            if (response.status === 201) {
                alert('Registration successful!');

                clearForm();
                router.push('/auth/login')
            } else {
                alert('Registration failed: ' + response.data.message);
            }
        })
        .catch(error => {
            console.error('There was an error during registration:', error);
            alert('An error occurred during registration. Please try again later.');
        });
}


</script>

<template>
    <v-row class="d-flex mb-3">
        <v-col cols="6">
            <v-label class="font-weight-bold mb-1">Name</v-label>
            <v-text-field variant="outlined" hide-details color="primary" v-model="name"></v-text-field>
        </v-col>
        <v-col cols="6">
            <v-label class="font-weight-bold mb-1">Surname</v-label>
            <v-text-field variant="outlined" hide-details color="primary" v-model="surname"></v-text-field>
        </v-col>
        <v-col cols="12">
            <v-label class="font-weight-bold mb-1">Email Address</v-label>
            <v-text-field variant="outlined" type="email" hide-details color="primary" v-model="email"></v-text-field>
        </v-col>
        <v-col cols="12">
            <v-label class="font-weight-bold mb-2">Role</v-label>
            <v-select
            variant="outlined"
            hide-details
            color="primary"
            label="Select"
            :items="['Student', 'Teacher']"
            v-model="role"
            ></v-select>
        </v-col>
        <v-col cols="12">
            <v-label class="font-weight-bold mb-1">Password</v-label>
            <v-text-field variant="outlined" type="password"  hide-details color="primary" v-model="password"></v-text-field>
        </v-col>
        <v-col cols="12" >
            <v-btn color="primary" size="large" block   flat @click="signUp()">Sign up</v-btn>
        </v-col>
    </v-row>
</template>
