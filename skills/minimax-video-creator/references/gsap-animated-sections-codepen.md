# GSAP Animated Sections — CodePen by GreenSock

> **Source:** (user-provided original source from CodePen XWzRraJ)
> **Effect:** 5 full-screen sections with scroll-triggered transitions, parallax backgrounds, and SplitText heading animations
> **Plugin:** GSAP + Observer + SplitText

## HTML

```html
<!--
Sections animate in and out on scroll. Scroll up or down and the sections will wrap around after hitting the start or end. Uses GSAP for the animations.
-->

<header>
  <div>Animated Sections</div>
  <div><a href="https://codepen.io/BrianCross/pen/PoWapLP">Original Inspiration</a></div>
</header>
<section class="first">
  <div class="outer">
    <div class="inner">
      <div class="bg one">
        <h2 class="section-heading">Scroll down</h2>
      </div>
    </div>
  </div>
</section>

<section class="second">
  <div class="outer">
    <div class="inner">
      <div class="bg">
        <h2 class="section-heading">Animated with GSAP</h2>
      </div>
    </div>
  </div>
</section>

<section class="third">
  <div class="outer">
    <div class="inner">
      <div class="bg">
        <h2 class="section-heading">GreenSock</h2>
      </div>
    </div>
  </div>
</section>

<section class="fourth">
  <div class="outer">
    <div class="inner">
      <div class="bg">
        <h2 class="section-heading">Animation platform</h2>
      </div>
    </div>
  </div>
</section>

<section class="fifth">
  <div class="outer">
    <div class="inner">
      <div class="bg">
        <h2 class="section-heading">Keep scrolling</h2>
      </div>
    </div>
  </div>
</section>
```

## CSS

```scss
$bg-gradient: linear-gradient(180deg, rgba(0, 0, 0, 0.6) 50%, rgba(0, 0, 0, 0.1) 100%);

* {
  box-sizing: border-box;
  user-select: none;
}

a {
  color: var(--color-surface-white);
  text-decoration: none;
}

body {
  margin: 0;
  padding: 0;
  height: 100vh;
  color: var(--light);
  text-transform: uppercase;
}

h2 {
  font-size: clamp(1rem, 6vw, 10rem);
  font-weight: 600;
  line-height: 1.2;
  text-align: center;
  margin-right: -0.5em;
  width: 90vw;
  max-width: 1200px;
  text-transform: none;
}

header {
  position: fixed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 5%;
  width: 100%;
  z-index: 3;
  height: 7em;
  font-size: clamp(0.66rem, 2vw, 1rem);
  letter-spacing: 0.5em;
}

section {
  height: 100%;
  width: 100%;
  top: 0;
  position: fixed;
  visibility: hidden;

  .outer,
  .inner {
    width: 100%;
    height: 100%;
    overflow-y: hidden;
  }

  .bg {
    display: flex;
    align-items: center;
    justify-content: center;
    position: absolute;
    height: 100%;
    width: 100%;
    top: 0;
    background-size: cover;
    background-position: center;

    h2 {
      z-index: 999;
    }

    .clip-text {
      overflow: hidden;
    }
  }
}

.first {
  .bg {
    background-image: $bg-gradient, url("https://assets.codepen.io/16327/site-landscape-1.jpg");
  }
}
.second {
  .bg {
    background-image: $bg-gradient, url("https://assets.codepen.io/16327/site-landscape-2.jpg");
  }
}
.third {
  .bg {
    background-image: $bg-gradient, url("https://assets.codepen.io/16327/site-landscape-3.jpg");
  }
}
.fourth {
  .bg {
    background-image: $bg-gradient, url("https://assets.codepen.io/16327/site-landscape-4.jpg");
  }
}
.fifth {
  .bg {
    background-image: $bg-gradient, url("https://assets.codepen.io/16327/site-landscape-5.jpg");
    background-position: 50% 45%;
  }
}

h2 * {
  will-change: transform;
}
```

## JavaScript (GSAP)

```javascript
gsap.registerPlugin(Observer);

let sections = document.querySelectorAll("section"),
  images = document.querySelectorAll(".bg"),
  headings = gsap.utils.toArray(".section-heading"),
  outerWrappers = gsap.utils.toArray(".outer"),
  innerWrappers = gsap.utils.toArray(".inner"),
  splitHeadings = headings.map(
    (heading) => new SplitText(heading, { type: "chars,words,lines", linesClass: "clip-text" }),
  ),
  currentIndex = -1,
  wrap = gsap.utils.wrap(0, sections.length),
  animating;

gsap.set(outerWrappers, { yPercent: 100 });
gsap.set(innerWrappers, { yPercent: -100 });

function gotoSection(index, direction) {
  index = wrap(index);
  animating = true;
  let fromTop = direction === -1,
    dFactor = fromTop ? -1 : 1,
    tl = gsap.timeline({
      defaults: { duration: 1.25, ease: "power1.inOut" },
      onComplete: () => (animating = false),
    });

  if (currentIndex >= 0) {
    gsap.set(sections[currentIndex], { zIndex: 0 });
    tl.to(images[currentIndex], { yPercent: -15 * dFactor }).set(sections[currentIndex], {
      autoAlpha: 0,
    });
  }

  gsap.set(sections[index], { autoAlpha: 1, zIndex: 1 });

  tl.fromTo(
    [outerWrappers[index], innerWrappers[index]],
    {
      yPercent: (i) => (i ? -100 * dFactor : 100 * dFactor),
    },
    {
      yPercent: 0,
    },
    0,
  )
    .fromTo(images[index], { yPercent: 15 * dFactor }, { yPercent: 0 }, 0)
    .fromTo(
      splitHeadings[index].chars,
      {
        autoAlpha: 0,
        yPercent: 150 * dFactor,
      },
      {
        autoAlpha: 1,
        yPercent: 0,
        duration: 1,
        ease: "power2",
        stagger: {
          each: 0.02,
          from: "random",
        },
      },
      0.2,
    );

  currentIndex = index;
}

Observer.create({
  type: "wheel,touch,pointer",
  wheelSpeed: -1,
  onDown: () => !animating && gotoSection(currentIndex - 1, -1),
  onUp: () => !animating && gotoSection(currentIndex + 1, 1),
  tolerance: 10,
  preventDefault: true,
});

gotoSection(0, 1);
```

## Key Animation Principles for Remotion

1. **5 fixed full-screen sections**, sequential in timeline (NOT scroll-driven — timeline-driven)
2. **Outer wrapper slides in** from top/bottom (`yPercent: 100 → 0`)
3. **Inner wrapper slides from opposite direction** (`yPercent: -100 → 0`)
4. **Background image has parallax** (`yPercent: 15 → 0` during transition)
5. **SplitText heading**: each char/word animates in with `yPercent: 150 → 0`, `autoAlpha: 0 → 1`, stagger `0.02` from random
6. **Duration**: `1.25s` with `power1.inOut` easing
7. **Background gradient**: `linear-gradient(180deg, rgba(0,0,0,0.6) 50%, rgba(0,0,0,0.1) 100%)`

## Remotion Adaptation Notes

- Replace GSAP Observer (scroll-based) with Remotion `Sequence` (time-based)
- Replace SplitText with custom word/char splitting
- Replace `yPercent` with Remotion `interpolate` / `useTransform`
- Direction (`dFactor`) becomes fixed per transition (alternating ±1)
