/**
 * AI Assistant chat interaction controller with suggested chips and source tags.
 */

const AssistantModule = {
  initEvents() {
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const chips = document.querySelectorAll('.chip');

    form?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const question = input.value.trim();
      if (!question) return;

      input.value = '';
      await this.processQuestion(question);
    });

    chips.forEach(chip => {
      chip.addEventListener('click', () => {
        const q = chip.getAttribute('data-question');
        if (q) this.processQuestion(q);
      });
    });
  },

  async processQuestion(question) {
    this.appendMessage(question, 'user');
    const typingId = this.appendTypingIndicator();

    try {
      const response = await API.sendChatMessage(question);
      this.removeTypingIndicator(typingId);
      this.appendMessage(response.answer, 'assistant', response);
    } catch (err) {
      this.removeTypingIndicator(typingId);
      this.appendMessage(`Sorry, an error occurred: ${err.message}`, 'assistant');
    }
  },

  appendMessage(text, sender, meta = null) {
    const chatBody = document.getElementById('chat-messages');
    if (!chatBody) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${sender}`;

    const formattedText = text.replace(/\n/g, '<br>');

    let docsMarkup = '';
    if (meta && meta.retrieved_docs && meta.retrieved_docs.length > 0) {
      docsMarkup = `<div class="docs-tag">📑 Sources: ${meta.retrieved_docs.join(', ')}</div>`;
    }

    const timeStr = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });

    msgDiv.innerHTML = `
      <div class="message-content">
        ${formattedText}
        ${docsMarkup}
      </div>
      <div class="message-meta">${sender === 'user' ? 'You' : 'ParkSense AI'} • ${timeStr}</div>
    `;

    chatBody.appendChild(msgDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
  },

  appendTypingIndicator() {
    const chatBody = document.getElementById('chat-messages');
    if (!chatBody) return null;

    const id = `typing-${Date.now()}`;
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message assistant';
    msgDiv.id = id;
    msgDiv.innerHTML = `
      <div class="message-content" style="font-style: italic; color: #94a3b8;">
        ParkSense AI is processing... 🤖
      </div>
    `;
    chatBody.appendChild(msgDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
    return id;
  },

  removeTypingIndicator(id) {
    if (id) document.getElementById(id)?.remove();
  }
};

document.addEventListener('DOMContentLoaded', () => {
  AssistantModule.initEvents();
});
