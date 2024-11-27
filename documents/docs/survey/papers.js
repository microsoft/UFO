// Global variables
let papersTable;
let allPapers = [];
let platforms = new Set();

// Function to determine platform category
function getPlatformCategory(platform) {
    const platformLower = platform.toLowerCase();
    let category_list = [];
    if (platformLower.includes('android') || platformLower.includes('ios') || platformLower.includes('mobile')) {
        category_list.push('Mobile');
    }
    if (platformLower.includes('windows') || platformLower.includes('linux') || 
        platformLower.includes('macos') || platformLower.includes('desktop')) {
        category_list.push('Computer');
    }
    if (platformLower.includes('web') || platformLower.includes('browser')) {
        category_list.push('Web');
    }
    if (category_list.length != 1) {
        return 'Cross-platform';
    }
    return category_list[0];
}

// Function to extract platform from paper data
function extractPlatform(paper) {
    let platform = paper.Platform ? paper.Platform.toLowerCase() : '';
    
    // Replace platform strings with proper capitalization
    const replacements = [
        ['android', 'Android'],
        ['ios', 'iOS'],
        ['windows', 'Windows'],
        ['linux', 'Linux'],
        ['macos', 'macOS'],
        ['web', 'Web'],
        ['mobile', 'Mobile'],
        ['pc', 'Computer'],
        ['computer', 'Computer'],
        ['desktop', 'Computer'],
        ['ubuntu', 'Ubuntu'],
        ['xr', 'XR'],
    ];

    for (const [search, replace] of replacements) {
        platform = platform.split(search).join(replace);
    }

    // If platform is empty, return default values
    if (!platform) {
        return {
            raw: '-',
            category: 'Cross-platform'
        };
    }

    const category = getPlatformCategory(platform);
    console.log(`Platform: ${platform}, Category: ${category}`);
    
    return {
        raw: platform,
        category: category
    };
}

// Function to parse date
function parseDate(dateStr) {
    const months = {
        'january': 0, 'february': 1, 'march': 2, 'april': 3, 'may': 4, 'june': 5,
        'july': 6, 'august': 7, 'september': 8, 'october': 9, 'november': 10, 'december': 11
    };
    
    const parts = dateStr.toLowerCase().split(' ');
    if (parts.length === 2) {
        const month = months[parts[0]];
        const year = parseInt(parts[1]);
        if (!isNaN(month) && !isNaN(year)) {
            return new Date(year, month);
        }
    }
    return new Date(0); // fallback for invalid dates
}

// Function to load papers from JSON files
async function loadPapers(category = 'all') {
    try {
        if (category === 'all') {
            if (allPapers.length === 0) {
                const categories = ['survey', 'benchmark', 'dataset', 'models', 'framework', 'gui-testing', 'virtual-assistant'];
                for (const cat of categories) {
                    try {
                        console.log(`Loading data from data/${cat}.json`);
                        const response = await fetch(`data/${cat}.json`);
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        const data = await response.json();
                        console.log(`Loaded ${data.length} papers from ${cat}`);
                        
                        // Process each paper
                        data.forEach(paper => {
                            const platformInfo = extractPlatform(paper);
                            platforms.add(platformInfo.category);
                            allPapers.push({
                                ...paper,
                                RawPlatform: platformInfo.raw,
                                Platform: platformInfo.category,
                                category: cat.charAt(0).toUpperCase() + cat.slice(1).replace('-', ' ')
                            });
                        });
                    } catch (error) {
                        console.error(`Error loading ${cat}.json:`, error);
                    }
                }
                console.log(`Total papers loaded: ${allPapers.length}`);
                updatePlatformFilter();
            }
            return allPapers;
        } else {
            console.log(`Loading data for category: ${category}`);
            const response = await fetch(`data/${category}.json`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log(`Loaded ${data.length} papers`);
            
            return data.map(paper => {
                const platformInfo = extractPlatform(paper);
                platforms.add(platformInfo.category);
                return {
                    ...paper,
                    RawPlatform: platformInfo.raw,
                    Platform: platformInfo.category,
                    category: category.charAt(0).toUpperCase() + category.slice(1).replace('-', ' ')
                };
            });
        }
    } catch (error) {
        console.error('Error loading papers:', error);
        return [];
    }
}

// Function to update platform filter options
function updatePlatformFilter() {
    const select = document.getElementById('platformFilter');
    select.innerHTML = '<option value="">All Platforms</option>';
    ['Mobile', 'Computer', 'Web', 'Cross-platform'].forEach(platform => {
        if (platforms.has(platform)) {
            const option = document.createElement('option');
            option.value = platform;
            option.textContent = platform;
            select.appendChild(option);
        }
    });
}

// Function to initialize DataTable
function initializeDataTable(data) {
    console.log('Initializing DataTable with', data.length, 'papers');
    
    if (papersTable) {
        papersTable.destroy();
        $('#papers-table').empty();
    }

    papersTable = $('#papers-table').DataTable({
        data: data,
        columns: [
            { 
                data: 'Name', 
                title: 'Title',
                className: 'dt-head-left column-title'
            },
            { 
                data: 'RawPlatform', 
                title: 'Platform',
                className: 'dt-head-left column-platform'
            },
            { 
                data: 'Date', 
                title: 'Date',
                className: 'dt-head-left column-date'
            },
            { 
                data: 'Highlight', 
                title: 'Highlight',
                className: 'dt-head-left column-highlight'
            },
            { 
                data: null,
                title: 'Links',
                className: 'dt-head-left column-links',
                orderable: false,
                render: function(data, type, row) {
                    const paperBtn = row.Paper_Url ? 
                        `<a href="${row.Paper_Url}" target="_blank" class="btn btn-primary btn-sm action-btn">Paper</a>` : '';
                    const codeBtn = row.Code_Url && row.Code_Url !== '/' ? 
                        `<a href="${row.Code_Url}" target="_blank" class="btn btn-success btn-sm action-btn">Code</a>` : '';
                    return `<div class="button-container">${paperBtn}${codeBtn}</div>`;
                }
            },
            { 
                data: 'category', 
                title: 'Category',
                className: 'dt-head-left column-category'
            }
        ],
        pageLength: 10,
        lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
        order: [[2, 'desc']], // Sort by date by default
        responsive: true,
        dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
             '<"row"<"col-sm-12"tr>>' +
             '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
        buttons: [
            {
                extend: 'collection',
                text: 'Export',
                buttons: ['copy', 'excel', 'pdf']
            }
        ],
        language: {
            search: "Search papers:",
            lengthMenu: "Show _MENU_ papers per page",
            info: "Showing _START_ to _END_ of _TOTAL_ papers",
            infoEmpty: "No papers available",
            infoFiltered: "(filtered from _MAX_ total papers)"
        }
    });

    // Adjust columns on window resize
    $(window).on('resize', function() {
        papersTable.columns.adjust().responsive.recalc();
    });
}

// Document ready
$(document).ready(async function() {
    console.log('Document ready, loading initial data...');
    
    // Load initial data
    const papers = await loadPapers();
    console.log('Initial data loaded:', papers.length, 'papers');
    initializeDataTable(papers);

    // Sidebar toggle
    $('#sidebarCollapse').on('click', function() {
        $('#sidebar').toggleClass('active');
    });

    // Category selection
    $('#sidebar a').on('click', async function(e) {
        e.preventDefault();
        const category = $(this).data('category');
        
        // Skip if clicking on dropdown toggle
        if ($(this).hasClass('dropdown-toggle')) {
            return;
        }

        console.log('Category selected:', category);
        
        // Update active state
        $('#sidebar li').removeClass('active');
        $(this).closest('li').addClass('active');

        // Load and display papers
        const papers = await loadPapers(category);
        console.log('Category data loaded:', papers.length, 'papers');
        initializeDataTable(papers);
    });

    // Platform filter
    $('#platformFilter').on('change', function() {
        const platform = this.value;
        console.log('Selected platform:', platform);
        
        // Custom search function to match against the Platform (category) field
        $.fn.dataTable.ext.search.push(function(settings, searchData, index, rowData, counter) {
            if (!platform) {
                return true; // Show all if no platform selected
            }
            return rowData.Platform === platform; // Match against the category
        });
        
        papersTable.draw();
        $.fn.dataTable.ext.search.pop();
    });

    // Date range filter
    function updateDateFilter() {
        const startDate = $('#dateFilterStart').val();
        const endDate = $('#dateFilterEnd').val();
        
        $.fn.dataTable.ext.search.push(function(settings, searchData, index, rowData, counter) {
            const rowDate = parseDate(rowData.Date); // 2 is the Date column index
            
            let valid = true;
            if (startDate) {
                const [startYear, startMonth] = startDate.split('-');
                const filterStartDate = new Date(startYear, startMonth - 1);
                valid = valid && rowDate >= filterStartDate;
            }
            if (endDate) {
                const [endYear, endMonth] = endDate.split('-');
                const filterEndDate = new Date(endYear, endMonth - 1);
                valid = valid && rowDate <= filterEndDate;
            }
            return valid;
        });
        
        papersTable.draw();
        $.fn.dataTable.ext.search.pop();
    }

    $('#dateFilterStart, #dateFilterEnd').on('change', updateDateFilter);

    // Handle responsive sidebar
    $(window).resize(function() {
        if ($(window).width() <= 768) {
            $('#sidebar').addClass('active');
        }
    }).trigger('resize');
});
