<script setup lang="ts">
import { ref } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';
import { useGlobalStore } from '@/stores/globalStore';

const router = useRouter();
const config = useRuntimeConfig();
// @ts-ignore
const AUTH_API_URL = config.public.authApiUrl;

const globalStore = useGlobalStore();

const email = ref('');
const password = ref('');

function clearForm() {
    email.value = '';
    password.value = '';
}


function logIn() {
    if (!email.value || !password.value) {
        alert('Please fill in all fields.');
        return;
    }

    const loginFormData = new FormData();
    loginFormData.append('username', email.value);
    loginFormData.append('password', password.value);

    axios.post(AUTH_API_URL + '/authentication/login', loginFormData, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    }).then(response => {
        if (response.status === 200) {
            const jsonData = response.data;
            
            // Aggiorna lo store con i dati dell'utente usando le azioni
            globalStore.setUser(jsonData.user);
            globalStore.setTokens(jsonData.access_token, jsonData.refresh_token);
            
            clearForm();
            router.push('/'); // Redirect to the home page or dashboard
        } else {
            alert('Login failed: ' + response.data.message);
        }
    })
    .catch(error => {
        console.error('There was an error during login:', error);
        if (error.response?.data?.detail) {
            alert('Login failed: ' + error.response.data.detail);
        } else {
            alert('An error occurred during login. Please try again later.');
        }
});
}


</script>

<template>
    <v-row class="d-flex mb-3">
        <v-col cols="12">
            <v-label class="font-weight-bold mb-1">Email</v-label>
            <v-text-field variant="outlined" type="email" hide-details color="primary" v-model="email"></v-text-field>
        </v-col>
        <v-col cols="12">
            <v-label class="font-weight-bold mb-1">Password</v-label>
            <v-text-field variant="outlined" type="password"  hide-details color="primary" v-model="password"></v-text-field>
        </v-col>
        <v-col cols="12" class="pt-0">
            <v-btn color="primary" size="large" block flat @click="logIn()">Sign in</v-btn>
        </v-col>
    </v-row>
</template>
