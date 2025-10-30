// Toast notification functionality
export function showToast(message, isError = false, duration = 3000) {
    const toastBody = document.getElementById("toast-body");

    if (!toastBody) {
        console.error("Error: toast-body not found in the DOM!");
        return;
    }

    toastBody.innerText = message;

    const toastElement = document.getElementById("liveToast");
    if (!toastElement) {
        console.error("Error: liveToast not found in the DOM!");
        return;
    }

    toastElement.classList.remove("bg-success", "bg-danger");
    toastElement.classList.add(isError ? "bg-danger" : "bg-success");

    const toast = new bootstrap.Toast(toastElement, { delay: duration });
    toast.show();
} 