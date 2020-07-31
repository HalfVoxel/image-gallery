// Set up an intersection observer with some options
var observer = new IntersectionObserver(lazyLoad, {
    // where in relation to the edge of the viewport, we are observing
    rootMargin: "200px",

    // how much of the element needs to have intersected 
    // in order to fire our loading function
    threshold: 0.01
});

function lazyLoad(elements) {
    for (const item of elements) {
        if (item.intersectionRatio >= 0.01) {
            const image = item.target;
            console.log(image, image.intersectionRatio);
            // set the src attribute to trigger a load
            image.src = image.dataset.src;

            // stop observing this element. Our work here is done!
            observer.unobserve(image);
        };
    };
};

window.addEventListener('load', () => {
    // Tell our observer to observe all img elements with a "lazy" class
    var lazyImages = document.querySelectorAll('img.lazy');
    lazyImages.forEach(img => {
        observer.observe(img);
    });
});
