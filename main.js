// Animate on Scroll
AOS.init();

// Smooth Scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    document.querySelector(this.getAttribute('href')).scrollIntoView({
      behavior: 'smooth'
    });
  });
});

// Highlight Active Navigation
window.addEventListener('scroll', () => {
  const sections = document.querySelectorAll("section");
  let scrollPos = window.scrollY + 150;
  sections.forEach(section => {
    if (scrollPos >= section.offsetTop && scrollPos < section.offsetTop + section.offsetHeight) {
      document.querySelectorAll("nav a").forEach(link => {
        link.classList.remove("text-blue-600", "font-bold");
        if (link.getAttribute("href").substring(1) === section.getAttribute("id")) {
          link.classList.add("text-blue-600", "font-bold");
        }
      });
    }
  });
});

// Contact Form Submission
const form = document.getElementById("contactForm");
const successMsg = document.getElementById("success-msg");
form.addEventListener("submit", function (e) {
  e.preventDefault();
  successMsg.classList.remove("hidden");
  form.reset();
});

// Dark Mode Toggle
const toggle = document.getElementById("darkToggle");
toggle.addEventListener("click", () => {
  document.body.classList.toggle("dark");
});

// Chatbot: Toggle Chat Window
const chatToggle = document.getElementById("chatToggle");
const chatBox = document.getElementById("chatBox");

chatToggle.addEventListener("click", () => {
  chatBox.classList.toggle("hidden");
});

// Chatbot: Send and Receive Messages
const sendBtn = document.getElementById("sendChat");
const chatInput = document.getElementById("chatInput");
const chatMessages = document.getElementById("chatMessages");

sendBtn.addEventListener("click", async () => {
  const userMsg = chatInput.value.trim();
  if (!userMsg) return;

  // Display user message
  chatMessages.innerHTML += <div class="text-gray-800 bg-white rounded p-2 shadow-sm">🧑: ${userMsg}</div>;
  chatInput.value = "";
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Send message to backend
  try {
    const res = await fetch("https://your-backend.com/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMsg })
    });

    const data = await res.json();
    const botReply = data.reply || "Thanks for your feedback!";

    // Display bot reply
    chatMessages.innerHTML += <div class="text-blue-600 bg-blue-50 rounded p-2 shadow-sm">🤖: ${botReply}</div>;
    chatMessages.scrollTop = chatMessages.scrollHeight;
  } catch (error) {
    chatMessages.innerHTML += <div class="text-red-600">⚠ Error: Could not send message</div>;
  }
});