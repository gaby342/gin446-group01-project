# AI Development Log


## Interaction 1

- AI tool:

Claude Sonnet 5.5

My prompt:
    html
    
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GIN446 Grid Lab</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>My Web Project</h1>
    </header>

    <nav>
        <a href="#">Home</a>
        <a href="#">About</a>
        <a href="#">Services</a>
        <a href="#">Contact</a>
    </nav>

    <main class="cards">
        <section class="card"><h2>Card 1</h2><p>Content goes here.</p></section>
        <section class="card"><h2>Card 2</h2><p>Content goes here.</p></section>
        <section class="card"><h2>Card 3</h2><p>Content goes here.</p></section>
        <section class="card"><h2>Card 4</h2><p>Content goes here.</p></section>
        <section class="card"><h2>Card 5</h2><p>Content goes here.</p></section>
        <section class="card"><h2>Card 6</h2><p>Content goes here.</p></section>
    </main>

    <footer>GIN446 Web Programming</footer>
</body>
</html>



 css

*{
    margin: 0;
    padding: 0;
    box-sizing: border-box;

}

nav{
    display: flex;
    flex-direction: row;
    justify-content:space-around;
    height: 75px;
    align-items: center;
    margin-top:3rem;
    margin-bottom: 5rem;
    background-color: indigo;
    color: white;
}

.cards {
    display: grid;
    grid-template-columns: 300px 300px 300px;
    gap: 30px;
    width: 100%;
    background-color: tomato;
}





You are a Frontend Web Dev, without writing or changing any of my code. Explain why a horizontal overflow may occur? Use a clear and beginner friendly explanation




- AI recommendation:

Fixed-size layout elements cause horizontal scrolling on narrow screens because they cannot shrink to fit the viewing area, even if their container is set to 100% width. To prevent this overflow, you must use flexible sizes rather than hard-coded pixel widths. Additionally, there is a minor syntax error with an extra closing bracket after the `.cards` class that should be removed.

- My Prompt: 

Suggest possible corrections, giving a detailed and clear explanation on why your correction actually solves the problem and makes the cards dyanmic

- AI recommendation:

Instead of forcing boxes to be a specific width, it tells the browser to automatically calculate how many boxes can fit on the screen (auto-fit).

Each card is given a minimum width of 250 pixels, but is allowed to stretch and share any leftover space equally (1fr). When the screen gets too narrow, the browser simply drops the extra cards down to the next row instead of pushing them off the edge. For extreme safety on very tiny screens, an advanced version (min(250px, 100%)) ensures the boxes never force themselves to be wider than the device itself.


- My decision:

ACCEPT

- Why:

I accepted it because auto-fit and minmax() make the cards responsive and prevent horizontal scrolling on smaller screens.

- Verification:
I checked the layout on different screen sizes. The cards now resize and move to new rows instead of causing horizontal scrolling.

- What I learned:

Fixed pixel widths can create overflow on small screens. Using auto-fit, minmax(), and flexible widths makes the layout responsive.

auto-fit fits as many columns as possible.
minmax() sets the smallest and largest size each column can have.
fr units allow the cards to share leftover (after taking into consideration the gap size) space in terms of fractions.


## Interaction 2

- AI tool:

Claude Sonnet 5.5

My prompt:
 
create a complete responsive css grid website for me


- AI recommendation:

I built Orbit, a Solar System explorer site, as something fresh. Open it from the publish card above.

Think of the layout as a city map. I named each zone (header, hero, planets, facts, news, footer), then told the grid where each zone lives on different screens:

Phone: one column, stacked like a scroll.
Tablet: two columns, with facts and news side by side.
Desktop: a 12-column layout, with the planet cards on the left and facts and news in a sidebar.

The planet cards use auto-fit, so they automatically wrap to however many fit, like books on a shelf that rearrange themselves when you resize it.

It also follows your device’s light or dark mode, and I assumed a simple, text-first design to keep it quick to load.

I can swap the topic, change the colors, or add a contact form or image gallery. Just say which.


- My decision:

Reject

- Why: 

The code is complex and hard to understand by itself

- Verification:

Changing one feature requires a lot of work and understanding of the code. It is not beginner friendly.

- What I learned:

AI prompting should be clear and specific. Complex code is not suitable for beginners. It's better to ask for simpler, modular code that can be easily understood and modified, and to use AI as a tutor and helper.



