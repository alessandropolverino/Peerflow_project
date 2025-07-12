<script setup lang="ts">
import { ref } from 'vue';
import UiParentCard from '@/components/shared/UiParentCard.vue';
import { useGlobalStore } from '@/stores/globalStore';
import { storeToRefs } from 'pinia';

const globalStore = useGlobalStore();
const {user} = storeToRefs(globalStore);

const handleLogout = () => {
  globalStore.logout();
  navigateTo('/auth/login');
};

</script>
<template>
    <v-row>
        <v-col cols="12" md="12">
            <UiParentCard title="PeerFlow Dashboard" class="mx-auto"> 
                <div class="pa-7 pt-1">
                    <p class="text-body-1" v-if="globalStore.isAuthenticated()">
                        Welcome, {{ globalStore.userName }}! 
                        <br>Role: {{ globalStore.userRole }}
                    </p>
                    
                    <v-btn 
                        v-if="globalStore.isAuthenticated()"
                        color="error" 
                        class="mt-4" 
                        @click="handleLogout"
                    >
                        Logout
                    </v-btn>
                </div>
            </UiParentCard>
        </v-col>
    </v-row>
</template>
