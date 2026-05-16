const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const openCameraBtn = document.getElementById("openCameraBtn");
const captureBtn = document.getElementById("captureBtn");
const uploadedPhoto = document.getElementById("uploadedPhoto");
const languageSelect = document.getElementById("languageSelect");

let stream = null;

// Open Camera
openCameraBtn.addEventListener("click", async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    video.style.display = "block";
    uploadedPhoto.style.display = "none";
    captureBtn.style.display = "inline-block";
  } catch (err) {
    alert("Camera access denied or not available");
  }
});

// Capture Image & Send to Backend
captureBtn.addEventListener("click", () => {
  const context = canvas.getContext("2d");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  context.drawImage(video, 0, 0);

  // Convert to image preview
  const imageDataURL = canvas.toDataURL("image/jpeg");
  uploadedPhoto.src = imageDataURL;
  uploadedPhoto.style.display = "block";

  // Stop camera
  stream.getTracks().forEach(track => track.stop());
  video.style.display = "none";
  captureBtn.style.display = "none";

  // Convert to blob and send
  canvas.toBlob(blob => {
    const formData = new FormData();
    formData.append("image", blob, "camera.jpg");
    formData.append("language", languageSelect.value); // ✅ Dynamic language

    captionDiv.innerText = "Analyzing captured image...";
    translatedDiv.innerText = "";
    captionsList.innerHTML = "";

    fetch("/caption", {
      method: "POST",
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      captionDiv.innerText = "Best Description: " + data.best_caption;

      // Dynamic Translation
      if (data.language !== "en" && data.translated_caption) {
        translatedDiv.innerText = "Translated: " + data.translated_caption;
        speakTranslatedBtn.style.display = "inline-block";
      } else {
        translatedDiv.innerText = "";
      }

      data.all_captions.forEach((cap, i) => {
        const p = document.createElement("p");
        p.innerText = `${i + 1}. ${cap}`;
        captionsList.appendChild(p);
      });

      speakBtn.style.display = "inline-block";
    });
  }, "image/jpeg");
});
