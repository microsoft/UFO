// Initialize Mermaid for ReadTheDocs theme
(function() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMermaid);
    } else {
        initMermaid();
    }

    function initMermaid() {
        // Initialize Mermaid
        if (typeof mermaid !== 'undefined') {
            mermaid.initialize({
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose',
                flowchart: {
                    useMaxWidth: true,
                    htmlLabels: true,
                    curve: 'basis'
                },
                sequence: {
                    useMaxWidth: true,
                    wrap: true
                },
                gantt: {
                    useMaxWidth: true
                }
            });
        }
    }
})();

