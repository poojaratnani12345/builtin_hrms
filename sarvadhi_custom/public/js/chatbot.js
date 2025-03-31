document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM fully loaded");

    if (typeof frappe !== 'undefined' && window.location.pathname === '/app/build') {
        console.log("Build page loaded");

        let searchBar = document.querySelector('input[data-element="search"]');
        if (searchBar) {
            let chatbotBtn = document.createElement('button');
            chatbotBtn.innerText = '💬';
            chatbotBtn.style.cssText = `
                background-color: #007bff;
                color: #fff;
                border: none;
                padding: 5px 10px;
                margin-left: 10px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            `;
            chatbotBtn.onclick = function() {
                openChatbox();
            };

            searchBar.parentNode.appendChild(chatbotBtn);
        }
    }
});

function openChatbox() {
    if (document.getElementById('chatbot')) return;

    let chatbot = document.createElement('div');
    chatbot.id = 'chatbot';
    chatbot.innerHTML = `
        <input type="text" id="chatbot-input" placeholder="Enter Doctype..." />
        <button onclick="redirectToDoctype()">Go</button>
    `;
    chatbot.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #f8f9fa;
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 9999;
    `;

    document.body.appendChild(chatbot);
}

function redirectToDoctype() {
    let input = document.getElementById('chatbot-input').value.trim();
    if (input) {
        frappe.call({
            method: 'sarvadhi_custom.custom_api.check_doctype',
            args: { doctype_name: input },
            callback: function(r) {
                if (r.message) {
                    window.location.href = `/app/${input.replace(/\s+/g, '-')}`;
                } else {
                    frappe.msgprint(`${input} Doctype does not exist.`);
                }
            }
        });
    }
}
