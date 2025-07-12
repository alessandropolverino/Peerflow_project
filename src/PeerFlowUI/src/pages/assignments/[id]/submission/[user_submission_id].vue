<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import UiParentCard from '@/components/shared/UiParentCard.vue';
import { useGlobalStore } from '@/stores/globalStore';
import { storeToRefs } from 'pinia';
import axios from 'axios';




const route = useRoute();
const globalStore = useGlobalStore();
const config = useRuntimeConfig();
// @ts-ignore
const PEERFLOW_API_URL = config.public.peerflowApiUrl;
// @ts-ignore
const FILE_STORAGE_URL = config.public.fileStorageUrl;

const {assignment, peerReview, assignmentSubmissions} = storeToRefs(globalStore);

const submissionId = route.params.user_submission_id;

const submissionStudent = computed(() => {
  const submission =  assignmentSubmissions.value.find((submission:any) => submission.id === submissionId);
  return assignment.value.involvedStudents.find((student:any) => student.id === submission?.StudentID);
});

const submissionToView = computed(() => {
  const userSubmission = assignmentSubmissions.value.find((submission:any) => submission.id === submissionId);
  if (userSubmission) {
    return {
      text: userSubmission.TextContent || '',
      files: userSubmission.Attachments.map((file:any) => ({
        name: file.FileName,
        url: `${FILE_STORAGE_URL}/buckets/${file.FileReference}`
      }))
    };
  }
  return { text: '', files: [] };
});

onMounted(() => {
  globalStore.fetchAssignment(PEERFLOW_API_URL, route.params.id, false);
});
</script>

<template>

  <v-row class="mb-4">
    <v-col cols="12">
      <h1>Submission Details</h1>
      <UiParentCard :title="`Submission by Student: ${submissionStudent?.name} <${submissionStudent?.email}>`" />
    </v-col>
  </v-row>  

  <v-form>
    <v-textarea
      v-model="submissionToView.text"
      label="Submission Text"
      outlined
      readonly
    ></v-textarea>

    <div>
      <h4>Uploaded Files</h4>
      <ul>
        <li v-for="file in submissionToView.files" :key="file.name">
          <a :href="file.url" target="_blank" rel="noopener noreferrer">{{ file.name }}</a>
        </li>
      </ul>
    </div>
  </v-form>

</template>