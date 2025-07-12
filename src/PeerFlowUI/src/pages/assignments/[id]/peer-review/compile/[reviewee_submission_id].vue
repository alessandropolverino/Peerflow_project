<template>

  <div>

    <UiParentCard title="Assignment Details">
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


        <v-col cols="12" v-if="submission != null">
          <h3 class="text-h6 my-5">Reviewing Submission:</h3>
          <v-form>
            <v-textarea
              v-model="submission.TextContent"
              label="Submission Text"
              outlined
              readonly
            ></v-textarea>

            <div>
              <h4>Uploaded Files</h4>
              <ul>
                <li v-for="file in submission.Attachments" :key="file.name">
                  <a :href="file.url" target="_blank" rel="noopener noreferrer">{{ file.name }}</a>
                </li>
              </ul>
            </div>
          </v-form>
        </v-col>
      </v-row>

      
    </UiParentCard>

    <UiParentCard title="Peer Review Rubric">
      <v-row v-if="peerReview?.Rubric?.Criteria && currentPairing?.ReviewResults?.PerCriterionScoresAndJustifications">
        <v-col cols="12" v-for="criterion in peerReview.Rubric.Criteria" :key="criterion.Title">
          <v-row class="align-center">
            <v-col cols="3">
              <h4 class="text-h6">{{ criterion.Title }}</h4>
            </v-col>
            <v-col cols="5">
              <p>{{ criterion.Description }}</p>
            </v-col>
            <v-col cols="2">
              <p>Range: {{ criterion.MinScore }} - {{ criterion.MaxScore }}</p>
            </v-col>
            <v-col cols="2">
              <v-text-field
                v-if="currentPairing?.ReviewResults?.PerCriterionScoresAndJustifications[criterion.Title]"
                v-model.number="currentPairing.ReviewResults.PerCriterionScoresAndJustifications[criterion.Title].Score"
                type="number"
                :min="criterion.MinScore"
                :max="criterion.MaxScore"
                label="Score"
                @input="(event: Event) => {
                  const value = (event.target as HTMLInputElement).value;
                  console.log('Score input:', value);
                  if (currentPairing?.ReviewResults) {
                    const parsedValue = parseFloat(value);
                    if (!isNaN(parsedValue)) {
                      currentPairing.ReviewResults.PerCriterionScoresAndJustifications[criterion.Title].Score = Math.max(criterion.MinScore, Math.min(criterion.MaxScore, parsedValue));
                    } else {
                      currentPairing.ReviewResults.PerCriterionScoresAndJustifications[criterion.Title].Score = criterion.MinScore;
                    }
                  }
                }"
                outlined
              ></v-text-field>
            </v-col>

            <v-col cols="12">
              <v-textarea
                v-if="currentPairing?.ReviewResults?.PerCriterionScoresAndJustifications[criterion.Title]"
                v-model="currentPairing.ReviewResults.PerCriterionScoresAndJustifications[criterion.Title].Justification"
                label="Feedback"
                outlined
                rows="2"
                placeholder="Enter feedback for this criterion"
              ></v-textarea>
            </v-col>
          </v-row>
        </v-col>
      </v-row>
      <v-row v-else>
        <v-col cols="12">
          <p>No rubric criteria available.</p>
        </v-col>
      </v-row>
    </UiParentCard>

    <v-btn @click="validateAndSendPeerReview" color="primary">Submit Peer Review</v-btn>
  </div>


</template>

<script setup lang="ts">
import UiParentCard from '@/components/shared/UiParentCard.vue';


import { type PeerReviewAssignment, type Assignment, type PRPairing } from '@/stores/globalStore';
import {routerKey, useRoute, useRouter } from 'vue-router';
import { useGlobalStore } from '@/stores/globalStore';
import axios from "axios";

const config = useRuntimeConfig();
//@ts-ignore
const PEERFLOW_API_URL = config.public.peerflowApiUrl;
// @ts-ignore
const FILE_STORAGE_URL = config.public.fileStorageUrl;
const route = useRoute();
const router = useRouter();
const globalStore = useGlobalStore();
const assignment_id = route.params.id;
const submission_id = route.params.reviewee_submission_id;



const peerReview = ref<PeerReviewAssignment | null>(null);
const assignment = ref<Assignment | null>(null);
const currentPairing = ref<PRPairing | null>(null);
const submission: any = ref(null);


const fetchPRAssignmentData = () => {
  axios.get(`${PEERFLOW_API_URL}/api/v1/assignments/${assignment_id}/peer-review`,
    {
      params: {
        submission_id: submission_id
      },
      headers: {
        'Authorization': `Bearer ${globalStore.access_token}`
      }
    }
  )
    .then(response => {

      if (response.status !== 200) {
        throw new Error(`Failed to fetch peer review assignment data: ${response.status}`);
      }
      peerReview.value = response.data.peerReviewAssignment;
      if (peerReview.value) {
        peerReview.value.Rubric = response.data.rubric;
      }
      assignment.value = response.data.assignment;
      submission.value = response.data.submission;

      if (submission.value && submission.value.Attachments) {
        submission.value.Attachments = submission.value.Attachments.map((attachment: any) => ({
          name: attachment.FileName,
          url: `${FILE_STORAGE_URL}/buckets/${attachment.FileReference}`
        }));
      }

      console.log("Assignment Data:", assignment.value);
      console.log("Peer Review Data:", peerReview.value);

      currentPairing.value = peerReview.value?.PeerReviewPairings
        .find((pairing: PRPairing) => 
        pairing.RevieweeSubmissionID === submission_id 
        && pairing.ReviewerStudentID === globalStore.user.id) ?? null;
      
      if (currentPairing.value) {
        currentPairing.value.ReviewResults = {
          "PerCriterionScoresAndJustifications": {}
        }
        peerReview.value?.Rubric.Criteria.forEach((criterion: any) => {
          //@ts-ignore
          currentPairing.value.ReviewResults.PerCriterionScoresAndJustifications[criterion.Title] = {
            Score: 0,
            Justification: ''
          };
        });

      }
      console.log("Current Pairing:", currentPairing.value);
    })
    .catch(error => {
      console.error("Error fetching peer review assignment data:", error);
    });
}

const sendCompiledPeerReview = () => {

  const pairingToSend: Record<string, any> = currentPairing.value as Record<string, any>;
  pairingToSend.ReviewResults.ReviewTimestamp = new Date().toISOString();
  pairingToSend.RevieweeStudentID = submission.value.StudentID;

  console.log("sending payload:", {
      PeerReviewID: peerReview.value?.id,
      Pairing: pairingToSend
    })
  

  axios.post(`${PEERFLOW_API_URL}/api/v1/assignments/${assignment_id}/peer-review/submit`,
    {
      PeerReviewID: peerReview.value?.id,
      Pairing: pairingToSend
    },
    {
      headers: {
        'Authorization': `Bearer ${globalStore.access_token}`
      }
    }
  )
    .then(response => {
      if (response.status === 201) {
        alert("Peer review submitted successfully!");
        router.push("/");
      } else {
        console.error("Failed to compile peer review:", response.status);
      }
    })
    .catch(error => {
      console.error("Error compiling peer review:", error);
    });

}

const validateAndSendPeerReview = () => {
  if (!currentPairing.value || !currentPairing.value.ReviewResults) {
    alert("Review results are not available.");
    return;
  }

  const missingScores = peerReview.value?.Rubric.Criteria.some(criterion => {
    const score = currentPairing.value?.ReviewResults?.PerCriterionScoresAndJustifications[criterion.Title]?.Score;
    const justification = currentPairing.value?.ReviewResults?.PerCriterionScoresAndJustifications[criterion.Title]?.Justification;
    return score === undefined || justification?.trim() === "";
  });

  if (missingScores) {
    alert("Please complete all scores and feedback before submitting.");
    return;
  }

  sendCompiledPeerReview();
};

onMounted(() => {
  fetchPRAssignmentData();
})
</script>