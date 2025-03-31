// // Copyright (c) 2025, sarvadhi and contributors
// // For license information, please see license.txt

// // frappe.ui.form.on("chatbot", {
// // 	refresh(frm) {

// // 	},
// // });
// frappe.ui.form.on('Chatbot', {
//     user_data: function(frm) {
//         let input = frm.doc.user_data.trim();

//         if (input) {
//             // Call backend to check if Doctype exists
//             frappe.call({
//                 method: 'sarvadhi_custom.sarvadhi_custom.doctype.chatbot.chatbot.chatbot',
//                 args: {
//                     doctype_name: input
//                 },
//                 callback: function(r) {
//                     if (r.message) {
//                         // Redirect to the doctype page if exists
//                         window.location.href = `/app/${input.replace(/\s+/g, '-')}`;
//                     } else {
//                         frappe.msgprint(`${input} Doctype does not exist.`);
//                     }
//                 }
//             });
//         } else {
//             frappe.msgprint("Please enter a valid input.");
//         }
//     }
// });
// Copyright (c) 2025, sarvadhi and contributors
// For license information, please see license.txt

frappe.ui.form.on('chatbot', {
    user_data: function(frm) {
        let input = frm.doc.user_data.trim();

        if (input) {
            // Call backend to check if Doctype exists
            frappe.call({
                method: 'sarvadhi_custom.sarvadhi_custom.doctype.chatbot.chatbot.check_doctype',
                args: {
                    doctype_name: input
                },
                callback: function(r) {
                    if (r.message) {
                        // Redirect to the doctype page if exists
                        window.location.href = `/app/${input.replace(/\s+/g, '-')}`;
                    } else {
                        frappe.msgprint(`${input} Doctype does not exist.`);
                    }
                }
            });
        } else {
            frappe.msgprint("Please enter a valid input.");
        }
    },

    after_save: function(frm) {
        let input = frm.doc.user_data.trim();

        if (input) {
            // Call backend to check if Doctype exists
            frappe.call({
                method: 'sarvadhi_custom.sarvadhi_custom.doctype.chatbot.chatbot.check_doctype',
                args: {
                    doctype_name: input
                },
                callback: function(r) {
                    if (r.message) {
                        // Redirect to the doctype page if exists
                        window.location.href = `/app/${input.replace(/\s+/g, '-')}`;
                    } else {
                        frappe.msgprint(`${input} Doctype does not exist.`);
                    }
                }
            });
        } else {
            frappe.msgprint("Please enter a valid input.");
        }
    }
});
