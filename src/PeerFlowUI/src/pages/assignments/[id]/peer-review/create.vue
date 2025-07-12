<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import UiParentCard from '@/components/shared/UiParentCard.vue';
import axios from 'axios';
import { useGlobalStore } from '@/stores/globalStore';
import { storeToRefs } from 'pinia';

const config = useRuntimeConfig();
// @ts-ignore
const PEERFLOW_API_URL = config.public.peerflowApiUrl;

const route = useRoute();
const router = useRouter();
const globalStore = useGlobalStore();
const assignmentId = route.params.id as string;

// Define types
interface Student {
  id: string;
  name: string;
  email: string;
}

interface Submission {
  id: string;
  SubmissionTimestamp: string;
  StudentID: string;
  AssignmentID: string;
  TextContent: string | null;
  Attachments: Array<{
    FileName: string;
    FileType: string;
    FileReference: string;
  }> | null;
}

interface PRPairing {
  ReviewerStudentID: string | null;
  RevieweeSubmissionID: string | null;
  RevieweeStudentID: string | null;
  Status: string;
}

interface PeerReviewDetail {
  NumberOfReviewersPerSubmission: number | null;
  ReviewDeadline: string | null;
  ReviewerAssignmentMode: 'random' | 'manual';
  PeerReviewPairings: PRPairing[];
  Rubric: {
    Criteria: Array<{
      Title: string;
      Description: string;
      MinScore: number | null;
      MaxScore: number | null;
    }>;
  };
}


const peerReviewDetails = ref<PeerReviewDetail>({
  NumberOfReviewersPerSubmission: 1, 
  ReviewDeadline: null,
  ReviewerAssignmentMode: 'random',
  PeerReviewPairings: [], // Initialize as an empty array
  Rubric: {
    Criteria: [], // Initialize as an empty array
  },
});

const { assignment, assignmentSubmissions }: { assignment: Ref<any>; assignmentSubmissions: Ref<Submission[]> } = storeToRefs(globalStore);




// ---- FUNCTIONS

function addCriterion() {
  peerReviewDetails.value.Rubric.Criteria.push({
    Title: '',
    Description: '',
    MinScore: null,
    MaxScore: null,
  });
}

function removeCriterion(index: number) {
  peerReviewDetails.value.Rubric.Criteria.splice(index, 1);
}

async function submitPeerReviewDetails() {
  // Prepara i dati nel formato richiesto dal backend
  const payload = {
    NumberOfReviewersPerSubmission: Number(peerReviewDetails.value.NumberOfReviewersPerSubmission),
    ReviewDeadline: peerReviewDetails.value.ReviewDeadline,
    ReviewerAssignmentMode: peerReviewDetails.value.ReviewerAssignmentMode,
    PeerReviewPairings: peerReviewDetails.value.PeerReviewPairings,
    Rubric: {
      Criteria: peerReviewDetails.value.Rubric.Criteria.map(criterion => ({
        Title: criterion.Title,
        Description: criterion.Description,
        MinScore: Number(criterion.MinScore),
        MaxScore: Number(criterion.MaxScore)
      }))
    }
  };

  try {
    const response = await axios.post(
      `${PEERFLOW_API_URL}/api/v1/assignments/${assignmentId}/peer-review`,
      payload,
      {
        headers: {
          'Authorization': `Bearer ${globalStore.access_token}`
        }
      }
    );

    if (response.status === 201) {
      globalStore.fetchAssignment(PEERFLOW_API_URL, assignmentId, true).then(() => {
        router.push(`/assignments/${assignmentId}/peer-review`);
      })
    } else {
      console.error('Failed to create peer review:', response.data);
    }
  } catch (error) {
    console.error('Error creating peer review:', error);
  }
}

function getUserStringByUserId(userId: string): string {
  const student = assignment.value.involvedStudents?.find((s: Student) => s.id === userId);
  return student ? `${student.name} <${student.email}>` : 'Unknown Student';
}

function getSubmitterUserStringBySubmissionId(submissionId: string | null): string {
  if (!submissionId) return 'Unknown Submitter';
  const submission = assignmentSubmissions.value.find((sub: Submission) => sub.id === submissionId);
  const userId = submission?.StudentID;
  return userId ? getUserStringByUserId(userId) : 'Unknown Submitter';
}

function getEligibleReviewersForSubmission(submission: Submission): Student[] {
  return assignment.value.involvedStudents?.filter((student: Student) => student.id !== submission.StudentID) || [];
}

function calculateRandomPairings() {
  const revPerSub = peerReviewDetails.value.NumberOfReviewersPerSubmission || 1;
  const pairings: PRPairing[] = [];

  console.log("Calculating random pairings")
  assignmentSubmissions.value.forEach((submission: Submission) => {
    const eligibleReviewers = getEligibleReviewersForSubmission(submission);

    if (!eligibleReviewers || eligibleReviewers.length === 0) {
      alert(`Nessun revisore idoneo trovato per la submission ${submission.id}`);
      console.error(`Nessun revisore idoneo trovato per la submission ${submission.id}`);
      return;
    }
    
    if (eligibleReviewers.length < revPerSub) {
      alert(`Non ci sono abbastanza revisori idonei per la submission ${submission.id}`);
      console.error(`Non ci sono abbastanza revisori idonei per la submission ${submission.id}`);
      return;
    }

    // Casually select reviewers (unique)
    const selectedReviewers = new Set<Student>();
    while (selectedReviewers.size < revPerSub) {
      const randomIndex = Math.floor(Math.random() * eligibleReviewers.length);
      const selectedReviewer = eligibleReviewers[randomIndex];

      // verify reviewer is not already selected for the submission
      if (!Array.from(selectedReviewers).some(reviewer => reviewer.id === selectedReviewer.id)) {
        selectedReviewers.add(selectedReviewer);
      }
    }

    // add pairing
    selectedReviewers.forEach(reviewer => {
      pairings.push({
        ReviewerStudentID: reviewer.id,
        RevieweeSubmissionID: submission.id,
        RevieweeStudentID: submission.StudentID,
        Status: 'pending'
      });
    });
  });

  peerReviewDetails.value.PeerReviewPairings = pairings;
}

const isFormValid = computed(() => {
  const details = peerReviewDetails.value;
  return (
    details.NumberOfReviewersPerSubmission !== null &&
    details.ReviewDeadline !== null &&
    details.ReviewerAssignmentMode !== null &&
    (details.ReviewerAssignmentMode === 'random' || details.PeerReviewPairings.every(pairing => pairing.ReviewerStudentID !== null)) &&
    details.Rubric.Criteria.length > 0 &&
    details.Rubric.Criteria.every(criterion =>
      criterion.Title.trim() !== '' &&
      criterion.Description.trim() !== '' &&
      criterion.MinScore !== null &&
      criterion.MaxScore !== null
    )
  );
});

onMounted(() => {
  globalStore.fetchAssignment(PEERFLOW_API_URL, assignmentId, true).then(() => {
      if(globalStore.assignment?.involvedStudents?.length <= 1) {
        alert("No sufficient students are involved in this assignment, cannot issue a new peer review!");
        router.push(`/assignments/${assignmentId}`);
      }

      calculateRandomPairings();
  })
});

</script>

<template>
  <v-row>
    <v-col cols="12">
      <UiParentCard title="Create Peer Review">
        <v-form @submit.prevent="">

          <v-text-field
            v-model="peerReviewDetails.NumberOfReviewersPerSubmission"
            label="Number of Reviewers per Submission"
            type="number"
            @change="calculateRandomPairings()"
            outlined
            required
          ></v-text-field>

          <v-col cols="12" md="6">
            <v-label class="font-weight-bold mb-1">Review Deadline</v-label>
            <v-text-field
              v-model="peerReviewDetails.ReviewDeadline"
              variant="outlined"
              hide-details="auto"
              color="primary"
              type="datetime-local"
            ></v-text-field>
          </v-col>

          <v-radio-group
            v-model="peerReviewDetails.ReviewerAssignmentMode"
            label="Reviewer Assignment Mode"
            outlined
            required
          >
            <v-radio label="Random Assignment" @click="calculateRandomPairings()" value="random"></v-radio>
            <v-radio label="Manual Assignment" value="manual"></v-radio>
          </v-radio-group>

          <div v-if="peerReviewDetails.ReviewerAssignmentMode === 'manual'">
            <h4>Manual Pairings</h4>
            <div v-for="(pairing, pairingIndex) in peerReviewDetails.PeerReviewPairings.sort((a, b) => (a.RevieweeSubmissionID || '').localeCompare(b.RevieweeSubmissionID || ''))" :key="pairingIndex">
              <h5>Submission by: {{ getSubmitterUserStringBySubmissionId(pairing.RevieweeSubmissionID) }}</h5>

              <v-select
                :items="getEligibleReviewersForSubmission(assignmentSubmissions.find((submission: Submission) => submission.id === pairing.RevieweeSubmissionID)!).map((student: Student) => ({ value: student.id, text: student.email }))"
                item-title="text"
                item-value="value"
                label="Select Reviewer"
                v-model="pairing.ReviewerStudentID"
                outlined
                required
              ></v-select>
            </div>
          </div>

          <h4>Rubric Criteria</h4>
          <div v-for="(criterion, index) in peerReviewDetails.Rubric.Criteria" :key="index">
            <v-text-field
              v-model="criterion.Title"
              label="Criterion Title"
              outlined
              required
            ></v-text-field>

            <v-textarea
              v-model="criterion.Description"
              label="Criterion Description"
              outlined
              required
            ></v-textarea>

            <v-text-field
              v-model="criterion.MinScore"
              label="Minimum Score"
              type="number"
              outlined
              required
            ></v-text-field>

            <v-text-field
              v-model="criterion.MaxScore"
              label="Maximum Score"
              type="number"
              outlined
              required
            ></v-text-field>

            <v-btn color="error" @click="removeCriterion(index)">Remove</v-btn>
          </div>
          <v-btn color="primary" @click="addCriterion">Add Criterion</v-btn>
          <div></div>
          <v-btn 
            type="submit" 
            color="primary" 
            class="ma-2" 
            @click="submitPeerReviewDetails" 
            :disabled="!isFormValid"
          >
            Create
          </v-btn>
        </v-form>
      </UiParentCard>
    </v-col>
  </v-row>
</template>

<style scoped>
/* Add any specific styles for the page here */
</style>
