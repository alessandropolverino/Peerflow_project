<template>
  <v-row>
    <v-col cols="12">
      <UiParentCard v-if="loading" title="Loading...">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
      </UiParentCard>

      <UiParentCard v-else-if="error" title="Error">
        <p>{{ error }}</p>
      </UiParentCard>

      <UiParentCard v-else title="Assignment Details">
        <v-row>
          <v-col cols="4">
            <h3 class="text-h6">Name</h3>
            <p>{{ assignment?.name }}</p>
          </v-col>

          <v-col cols="4">
            <h3 class="text-h6">Description</h3>
            <p>{{ assignment?.description }}</p>
          </v-col>

          <v-col cols="4">
            <h3 class="text-h6">Status</h3>
            <p>{{ assignment?.status }} <span v-if="globalStore.isTeacher()">({{ globalStore.assignmentSubmissions.length }} submissions)</span> </p>
          </v-col>

          <!-- Dates Row -->
          <v-col cols="12">
            <v-row>
              <v-col cols="12" md="4">
                <h3 class="text-h6">Created Date</h3>
                <p>{{ assignment ? new Date(assignment.createdDate).toLocaleString() : '' }}</p>
              </v-col>
              <v-col cols="12" md="4">
                <h3 class="text-h6">Last Modified Date</h3>
                <p>{{ assignment ? new Date(assignment.lastModifiedDate).toLocaleString() : '' }}</p>
              </v-col>
              <v-col cols="12" md="4">
                <h3 class="text-h6">Submission Deadline</h3>
                <p>{{ assignment ? new Date(assignment.submissonDeadline).toLocaleString() : '' }}</p>
              </v-col>
            </v-row>
          </v-col>
        </v-row>

        <TeacherView v-if="globalStore.isTeacher()" />

        <StudentView v-else />
      </UiParentCard>
    </v-col>
  </v-row>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import UiParentCard from '@/components/shared/UiParentCard.vue';
import TeacherView from '~/components/AssignmentTeacherView.vue';
import StudentView from '~/components/AssignmentStudentView.vue';
import { useGlobalStore } from '@/stores/globalStore';
import {storeToRefs} from 'pinia';

const config = useRuntimeConfig() 
// @ts-ignore
const PEERFLOW_API_URL = config.public.peerflowApiUrl;

const route = useRoute();
const globalStore = useGlobalStore();
const loading = ref(true);
const error = ref<string | null>(null);

const {assignment} = storeToRefs(globalStore);

onMounted(() => {
  globalStore.fetchAssignment(PEERFLOW_API_URL, route.params.id as string, true)
    .then(() => {
      loading.value = false;
    });
});
</script>

<style scoped>
.selected-students-container {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px; /* Increased padding for better spacing */
  background-color: #fafafa;
}

.selected-students-container::-webkit-scrollbar {
  width: 6px;
}

.selected-students-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.selected-students-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.selected-students-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Per Firefox */
.selected-students-container {
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f1f1f1;
}
</style>
