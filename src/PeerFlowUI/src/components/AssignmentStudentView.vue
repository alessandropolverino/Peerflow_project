<template>
  <v-row cols="12">

    


    <v-col cols="12">
      <UiParentCard title="Your Submission">


        <div v-if="submissionErrorCode && submissionErrorCode !== 404">
          <p>{{ submissionError }}</p>
        </div>

        <div v-else-if="submissionToView.text || submissionToView.files.length">
          <h3 class="text-h6 my-5">Your Submission</h3>
          <v-form>
            <v-textarea
              v-model="submissionToView.text"
              label="Submission Text"
              outlined
              readonly
            ></v-textarea>

            <div >
              <h4>Uploaded Files</h4>
              <ul v-if="submissionToView.files.length > 0">
                <li v-for="file in submissionToView.files" :key="file.name">
                  <a :href="file.url" target="_blank" rel="noopener noreferrer">{{ file.name }}</a>
                </li>
              </ul>
              <p v-else class="text-muted">No files uploaded.</p>
            </div>
          </v-form>
        </div>

        <div v-else-if="globalStore.assignment.status == 'Open Submission'">
          <h3 class="text-h6 my-5">Submit Your Assignment</h3>
          <v-form @submit.prevent="submitAssignment">
            <v-textarea
              v-model="submissionToSend.text"
              label="Submission Text *"
              outlined
              required
            ></v-textarea>

            <v-file-input
              v-model="submissionToSend.files"
              label="Upload Files"
              outlined
              multiple
              accept=".pdf,.txt,.jpg"
              chips
              show-size
            ></v-file-input>

            <p class="text-muted mb-2">Fields marked with * are required</p>

            <v-btn type="submit" color="primary" :disabled="!submissionToSend.text">Submit</v-btn>
          </v-form>
        </div>


        <div v-if="myPairings.length > 0" class="mb-5">
          <h4 class="text-h6 my-5">Your Peer Review Pairings</h4>

          <div v-for="pairing in myPairings" :key="pairing.RevieweeSubmissionID" class="mb-3">
            <p><strong>• Peer Review for submission:</strong> {{ pairing.RevieweeSubmissionID }}</p>
            <v-btn v-if="pairing.Status == 'pending'" :to="`/assignments/${route.params.id}/peer-review/compile/${pairing.RevieweeSubmissionID}`" color="primary" class="ml-3 ma-2 mb-2">
              View Peer Review
            </v-btn>
            <v-btn v-else disabled>
              Peer Review Completed
            </v-btn>

          </div>

        </div>

        <div v-if="results.resultsBySubmission || ( results.resultsByReview && results.resultsByReview.length > 0)" class="mb-5">
          <h2 class="text-3xl my-5">Peer Review Results</h2>

          <div v-if="results.resultsBySubmission">
            <h5 class="text-h6 my-3">Your Score</h5>
            <p>Overall Average Score: {{ results.resultsBySubmission.OverallAverageScore }}</p>

            <h5 class="text-h6 my-3">Criterion Scores</h5>
            <v-table>
              <thead>
                <tr>
                  <th>Criterion</th>
                  <th>Average Score</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(score, criterion) in results.resultsBySubmission.PerCriterionAverageScores" :key="criterion">
                  <td>{{ criterion }}</td>
                  <td>{{ score }}</td>
                </tr>
              </tbody>
            </v-table>
          </div>

          <div v-if="results.resultsByReview && results.resultsByReview.length > 0">
            <h5 class="text-h6 my-3">Review Results</h5>
            <v-table>
              <thead>
                <tr>
                  <th>Review #</th>
                  <th>Overall Average Score</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(review, index) in results.resultsByReview" :key="review.RevieweeSubmissionID">

                  <td>{{ index+1 }}</td>
                  <td>{{ review.OverallAverageScore }}</td>
                </tr>
              </tbody>
            </v-table>
          </div>
        </div>
      </UiParentCard>
  </v-col>
  </v-row>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useGlobalStore } from '@/stores/globalStore';
import axios from 'axios';

const route = useRoute();
const globalStore = useGlobalStore();
const config = useRuntimeConfig();
const PEERFLOW_API_URL = config.public.peerflowApiUrl;
const FILE_STORAGE_URL = config.public.fileStorageUrl;

const submissionError = ref<string | null>(null);
const submissionErrorCode = ref<number | null>(null);

const submissionToSend = ref({
  text: '',
  files: [] as File[]
});

const submissionToView = ref({
  text: '',
  files: [] as { name: string; url: string }[],
  id: ''
});

const myPairings: any = ref([]); 

interface ResBySubmission {
  SubmissionID: string;
  NumberOfAssignedReviews: number;
  NumberOfCompletedReviews: number;
  OverallAverageScore: number;
  PerCriterionAverageScores: Record<string, number>; // criterion name: average score
}

interface ResByReview {
  RevieweeSubmissionID: string;
  ReviewerStudentID: string;
  OverallAverageScore: number;
}

interface StudentResults {
  resultsBySubmission: ResBySubmission | null;
  resultsByReview: ResByReview[] | null;
}

const results = ref<StudentResults>({
  resultsBySubmission: null,
  resultsByReview: null
});

const fetchResults = () => {
  if (submissionToView.value.id.length > 1) {
    axios.get(`${PEERFLOW_API_URL}/api/v1/assignments/${route.params.id}/peer-review/results/student/${submissionToView.value.id}`, {
      headers: {
        'Authorization': `Bearer ${globalStore.access_token}`
      }
    }).then(response => {
      if (response.status === 200) {
        results.value.resultsBySubmission = response.data.resultsBySubmission;
        results.value.resultsByReview = response.data.resultsByReview;
      } else {
        console.error('Error fetching peer review results:', response.status);
      }
    }).catch(err => {
      console.error('Error fetching peer review results:', err);
    });
  }
}


const fetchSubmissionDetails = async () => {
  try {
    const response = await axios.get(`${PEERFLOW_API_URL}/api/v1/assignments/${route.params.id}/submission`, {
      params: {
        assignment_id: route.params.id,
      },
      headers: {
        'Authorization': `Bearer ${globalStore.access_token}`
      }
    });

    if (response.status === 200) {
      console.log("Submission details fetched successfully:", response.data);
      submissionToView.value = {
        id: response.data.submission.id,
        text: response.data.submission.TextContent || '',
        files: (response.data.submission.Attachments || []).map((attachment: { FileName: string; FileReference: string }) => ({
          name: attachment.FileName,
          url: `${FILE_STORAGE_URL}/buckets/${attachment.FileReference}`
        }))
      };
      submissionErrorCode.value = null;
      fetchResults(); // Fetch peer review results after fetching submission details
    } else {
      submissionErrorCode.value = response.status;
    }
  } catch (err: any) {
    if (err.response) {
      submissionErrorCode.value = err.response.status;
    } else {
      console.error('Error fetching submission details:', err);
      submissionErrorCode.value = null;
      submissionError.value = null;
    }
  }
};

const fetchMyPeerReviewPairings =  () => {
  axios.get(`${PEERFLOW_API_URL}/api/v1/assignments/${route.params.id}/peer-review/my-pairings`, {
    headers: {
      'Authorization': `Bearer ${globalStore.access_token}`
    }
  })
  .then(response => {
    if (response.status === 200) {
      myPairings.value = response.data.pairings;
      console.log(myPairings.value);
    } else {
      console.error('Error fetching peer review pairings:', response.status);
    }
  })
  .catch(err => {
    console.error('Error fetching peer review pairings:', err);
  });
}

const submitAssignment = async () => {
  try {
    const formData = new FormData();
    formData.append('text_content', submissionToSend.value.text);

    if (submissionToSend.value.files.length > 0) {
      submissionToSend.value.files.forEach((file) => {
        if (file instanceof File) {
          formData.append('files', file);
        } else {
          console.error('File non valido:', file);
        }
      });
    }

    const response = await axios.post(`${PEERFLOW_API_URL}/api/v1/assignments/${route.params.id}/submit`, formData, {
      headers: {
        'Authorization': `Bearer ${globalStore.access_token}`,
        'Content-Type': 'multipart/form-data'
      }
    });

    if (response.status === 201) {
      fetchSubmissionDetails(); // Refresh submission details after successful submission
      submissionErrorCode.value = null;
    } else {
      submissionErrorCode.value = response.status;
    }
  } catch (err: any) {
    console.error('Error submitting assignment:', err);
    if (err.response && err.response.data) {
      console.error('Server response:', err.response.data);
    }
    submissionErrorCode.value = null;
  }
};



onMounted(() => {
  fetchSubmissionDetails();
  fetchMyPeerReviewPairings();
})
</script>
