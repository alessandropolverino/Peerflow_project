<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { routerKey, useRoute, useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useGlobalStore, type PeerReviewAssignment, type Assignment } from '@/stores/globalStore';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const config = useRuntimeConfig();
// @ts-ignore
const PEERFLOW_API_URL = config.public.peerflowApiUrl;

const menu = ref(false);
const newDeadline = ref(null);
const deadlineRules = [
  (value: string) => !!value || 'Deadline is required',
  (value: string) => {
    const selectedDate = new Date(value);
    const now = new Date();
    return selectedDate > now || 'Deadline must be in the future';
  }
];

const globalStore = useGlobalStore();
const { assignment, peerReview }: { assignment: Ref<Assignment>; peerReview: Ref<PeerReviewAssignment | null> } = storeToRefs(globalStore);

const getStudentStringFromId = (userId: string) => {
  const student = globalStore.assignment?.involvedStudents.find((s: any) => s.id === userId);
  return student ? `${student.name} <${student.email}>` : 'Unknown Student';
};

const getSubmitterStudentStringFromId = (submissionId: string) => {
  const submission = globalStore.assignmentSubmissions?.find((sub: any) => sub.id === submissionId);
  const userId = submission?.StudentID;
  const student = globalStore.assignment?.involvedStudents.find((s: any) => s.id === userId);
  return student ? `${student.name} <${student.email}>` : 'Unknown Submitter';
};

const closePeerReview = () => {
  axios.patch(
    PEERFLOW_API_URL+"/api/v1/assignments/"+assignment.value.id+"/peer-review",
    {
      "ReviewDeadline": new Date().toISOString(),
    },
    {
      headers: {
        'Authorization': `Bearer ${globalStore.access_token}`
      }
    }
  ).then(response => {
    console.log("RISP CLOSED", response);
    if (response.status === 200) {
      setTimeout(() => {
        globalStore.fetchAssignment(PEERFLOW_API_URL, route.params.id, true);
        menu.value = false;
      }, 1000);
    } else {
      console.error('Failed to close peer review:', response.statusText);
    }
  }).catch(error => {
    console.error('Error closing peer review:', error);
  });
}

const reopenPeerReview = async () => {
  if (!newDeadline.value) return;

  axios.patch(
    PEERFLOW_API_URL+"/api/v1/assignments/"+assignment.value.id+"/peer-review", 
  {
    ReviewDeadline: new Date(newDeadline.value).toISOString(),
  }, {
    headers: {
      'Authorization': `Bearer ${globalStore.access_token}`
    }
  }).then(response => {
    if (response.status === 200) {
      console.log('response', response.data);
      globalStore.fetchAssignment(PEERFLOW_API_URL, route.params.id, true);
      menu.value = false;
    } else {
      console.error('Failed to reopen submission:', response.statusText);
    }
  }).catch(error => {
    console.error('Error reopening submission:', error);
  });
};

const startComputeResult = () => {
  axios.get(
    PEERFLOW_API_URL+"/api/v1/assignments/"+assignment.value.id+"/peer-review/start-compute-results",
    {
      headers: {
        'Authorization': `Bearer ${globalStore.access_token}`
      }
    }
  ).then(response => {
    console.log(response)
    if (response.status === 200) {
      alert('Compute of results started successfully. It may take a few minutes to complete.');
      router.push("/assignments/" + route.params.id);
    } else {
      console.error('failed to start compute of results: ', response.statusText)
    }
  }).catch(error => {
    console.error('Error starting compute results:', error);
  });
}

onMounted(() => {
  globalStore.fetchAssignment(PEERFLOW_API_URL, route.params.id, false);
});
</script>

<template>
  <v-row>

    <v-col cols="12">
      <h1>Peer Review</h1>
      <div v-if="peerReview == null">
          <p>Nessun dato di peer review disponibile.</p>
      </div>
    </v-col>

  </v-row>

  <v-row v-if ="peerReview != null">
    <v-col cols="6">
      <h3 class="text-h6">Assignment: </h3>
      <p>{{ assignment?.name }}</p>
    </v-col>
    <v-col cols="4">
      <h3 class="text-h6">Status: </h3>
      <p>{{ peerReview?.Status }}</p>
    </v-col>
    <v-col cols="6">
      <h3 class="text-h6">Peer Review Submission Deadline: </h3>
      <p>{{ peerReview?.ReviewDeadline }}</p>
    </v-col>

    <v-col cols="3" v-if="peerReview.Status == 'Peer Review Started'">
      <v-btn color="warning" @click="closePeerReview">
        Close Peer Review
      </v-btn>
    </v-col>
    <v-col cols="3" v-if="peerReview.Status == 'Peer Review Closed'">
      <v-menu
        v-model="menu"
        :close-on-content-click="false"
        transition="scale-transition"
        offset-y
        max-width="290px"
        min-width="290px"
      >
        <template v-slot:activator="{ props }">
          <v-btn color="primary" v-bind="props" class="mb-2">
            Reopen Peer Review
          </v-btn>
        </template>
        <v-card>
          <v-card-title>Select New Deadline</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="newDeadline"
              variant="outlined"
              hide-details="auto"
              color="primary"
              type="datetime-local"
              :rules="deadlineRules"
            ></v-text-field>
          </v-card-text>
          <v-card-actions>
            <v-btn text color="primary" @click="menu = false">Cancel</v-btn>
            <v-btn
              text
              color="primary"
              :disabled="!newDeadline || deadlineRules.some(rule => rule(newDeadline || '') !== true)"
              @click="reopenPeerReview"
            >
              Confirm
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-menu>
    </v-col>

    <v-col cols="3" v-if="peerReview.Status == 'Peer Review Closed'">
      <v-btn color="success" class="mb-2" @click="startComputeResult">
        Compute results
      </v-btn>
    </v-col>


    <v-col cols="12">
      <h3>Rubric Criteria</h3>

      <v-list>
        <v-list-item v-for="(criterion, index) in peerReview?.Rubric.Criteria" :key="index">
          <v-list-item-content>
            <v-list-item-title>Criterion title: {{ criterion.Title }}</v-list-item-title>
            <v-list-item-subtitle>Criterion description: {{ criterion.Description }}</v-list-item-subtitle>
            <v-list-item-subtitle>Vote range: {{ criterion.MinScore }} - {{ criterion.MaxScore }}</v-list-item-subtitle>
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-col>

    <v-col cols="12">
      <h3>Reviews: </h3>
      <v-list >
        <v-list-item 
          v-for="(pairing, pairing_index) in peerReview?.PeerReviewPairings" :key="pairing_index"
          class="border-left-grey mb-4"
          style="border-left: 2px solid grey;"
          >
          <v-list-item-content>
            <v-list-item-title>Reviewer: {{ getStudentStringFromId(pairing.ReviewerStudentID) }}</v-list-item-title>
            <v-list-item-title>Reviewee: {{ getSubmitterStudentStringFromId(pairing.RevieweeSubmissionID) }}</v-list-item-title>

            <v-list 
              v-if="pairing.ReviewResults && pairing.ReviewResults.PerCriterionScoresAndJustifications"
              >
              <v-list-item v-for="(result, criterionTitle) in pairing.ReviewResults.PerCriterionScoresAndJustifications" :key="criterionTitle">
                <v-list-item-content>
                  <v-list-item-title>Criterion: {{ criterionTitle }}</v-list-item-title>
                  <v-list-item-subtitle>Score: {{ result.Score }}</v-list-item-subtitle>
                  <v-list-item-subtitle>Justification: {{ result.Justification }}</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-list>

            <v-list v-else>
              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title>No review results available</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </v-list>

          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-col>

  </v-row>


</template>