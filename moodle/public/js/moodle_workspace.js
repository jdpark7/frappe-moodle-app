$(document).on('page-change', function () {
    console.log("Moodle Integration: Page Changed", frappe.get_route());
    // Log the actual route for debugging
    let route = frappe.get_route();
    console.log("Moodle Integration Route:", route);

    // Looser check: Is 'moodle' anywhere in the route?
    let is_moodle_page = route.some(segment => segment && segment.toString().toLowerCase() === 'moodle');

    if (is_moodle_page) {
        console.log("Moodle Integration: Matched! Rendering...");
        setTimeout(render_moodle_dashboard, 500);
    }
});

function render_moodle_dashboard() {
    let $page = $('.layout-main-section');
    if ($page.length === 0) return;

    let $container = $page.find('.moodle-dashboard-container');
    if ($container.length > 0) return; // Already rendered

    // Create container APTER the header/widgets usually?
    // Let's prepend to main section so it's at top, or append.
    $container = $('<div class="moodle-dashboard-container container-fluid my-4"></div>');

    // Find the widgets area and append AFTER it, or prepend to it?
    // Workspace usually has .codex-editor or .widget-group
    // Let's prepend it for visibility
    if ($page.find('.codex-editor').length > 0) {
        $container.insertBefore($page.find('.codex-editor'));
    } else {
        $page.append($container);
    }

    $container.html('<div class="text-center p-4">Loading Moodle Dashboard...</div>');

    frappe.call({
        method: 'moodle.moodle.api.dashboard.dashboard',
        callback: (r) => {
            if (r.message) {
                render_dashboard_content($container, r.message);
            } else {
                $container.html('<div class="alert alert-warning">Could not fetch dashboard data.</div>');
            }
        }
    });
}

function render_dashboard_content($container, data) {
    let html = `<h4>My Moodle Dashboard</h4><hr>`;

    if (data.error) {
        html += `<div class="alert alert-danger">${data.error}</div>`;
    } else if (data.courses && data.courses.length > 0) {
        html += `<div class="row">`;
        data.courses.forEach(course => {
            let progress = course.progress !== undefined ? `Progress: ${course.progress}%` : '';
            html += `
                <div class="col-md-4 mb-3">
                    <div class="card h-100 shadow-sm border">
                        <div class="card-body">
                            <h5 class="card-title">${course.fullname}</h5>
                            <h6 class="card-subtitle mb-2 text-muted">${course.shortname}</h6>
                            <p class="card-text">${progress}</p>
                            <a href="${course.viewurl}" class="btn btn-sm btn-primary" target="_blank">Go to Course</a>
                        </div>
                    </div>
                </div>`;
        });
        html += `</div>`;
    } else if (data.found_moodle_user) {
        html += `
             <div class="alert alert-warning">
                <h4>Connected as ${data.found_moodle_user.fullname}</h4>
                <p>No courses found.</p>
                <a href="${data.moodle_url}" class="btn btn-primary" target="_blank">Go to Moodle</a>
             </div>`;
    } else {
        html += `
             <div class="alert alert-warning">
                <h4>Account Not Linked</h4>
                <p>${data.account_warning || "No Moodle account found."}</p>
                <button class="btn btn-success" onclick="create_moodle_account_dialog()">Create Account</button>
             </div>`;
    }

    $container.html(html);
}

window.create_moodle_account_dialog = function () {
    let d = new frappe.ui.Dialog({
        title: 'Create Moodle Account',
        fields: [
            {
                label: 'Password',
                fieldname: 'password',
                fieldtype: 'Password',
                reqd: 1
            }
        ],
        primary_action_label: 'Create',
        primary_action(values) {
            frappe.call({
                method: 'moodle.www.dashboard.create_account',
                args: { password: values.password },
                callback: function (r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint("Account Created! Please log in with the password you just set.");
                        d.hide();
                        render_moodle_dashboard(); // Refresh
                    } else {
                        frappe.msgprint("Error: " + (r.message ? r.message.message : "Unknown"));
                    }
                }
            });
        }
    });
    d.show();
};
