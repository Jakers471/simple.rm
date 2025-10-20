# Questions Log

## 1

So if you were building a project in Cloud Code or in AI, and you could create multiple agents, and you can even run agents in parallel in terms of editing, writing documents, change logs, developing and writing code, writing tests, just everything. Think about coding and how developers work and think about industry standards. If you could create any number of agents to do different tasks in terms of from the start of a project to the end in the deployment of a project or code base, what agents would you create and why would you create them in order to make everything a smooth transition? How would you do it by industry standards?

## 2

What is a CI-CD pipeline?

## 3

So I don't, I don't understand that. I don't understand the, I don't even know how to ask this question. Staging and production code. So are you saying that you have, what, your code-based logic, right? So you have your code, BS code, whatever, and you create some files and folders, they all pass, and then you commit and you push them to Git? What is, fucking shit. And then, and then what? You go on different branches, there's like testing branches, live branches, like the main branch, I don't understand that. And then what? When things are passing, you merge the branch into the production ready branch? What does that even mean? That doesn't mean that, okay, I think I know what that means, actually.

## 4

## 5

Tell me very detailed what TB, Test Driven Development, is like real world. How do you use it? How do developers use it? I understand that it's like you make the tests, you make them fail, and then you write the logic to make the test green, and then once they're all passing or whatever, you refractor, you refractor it, you refactor it, or yeah, refractoring, it's a weird word. You're refractoring the core logic, not the test logic, correct? Like you're going back through the core or no, because test logic doesn't live inside the core logic. The test imports the core logic file. So what are you refractoring exactly? What's that like blue phase or whatever the fuck at the end? It's like green, red, blue, and then you.

## 6

Next question, when you were talking about that planning agent, or I guess, again, industry standards, when someone, let's say I wanted to hire someone, a developer, or a team, or let's just say a solo developer, right, and I sit down, and I'm someone who knows absolutely nothing about code, and he knows everything about code, so he sits down and he interviews me essentially, what do you want, what do you want to build, how do you want it to work, how does it function, all that stuff, what is he doing in that phase exactly, like what does the developer need concrete, what does he need to build out first, is he building out, is he thinking through all the different modules he's going to need, how they're all going to connect, is he figuring out how he's going to go about the testing phase, like is that main, number one, like planning, first thing that a developer would do is understanding everything he needs at the very beginning of the project, essentially creating a tree of everything he needs, placeholder, files, folders, again, industry standards, I don't know how they do it, how do developers normally go about this.

## 7

Once the architecture is built out, say you know all the features, you have all the files and folders, you have the whole skeleton laid out, how do they go then about coding? Where do they begin? Where do they start? What do they write first? What do they write next? Do they go one module at a time? How do they connect them? I know there's integration testing. Is this where the TDD drive or the TDD workflow comes into place? The way that I understand it would be you map out the architecture, all the files and folders you need, and then you go about creating which file first though. The main entry point, do you start with smaller modules? Do you start with the core modules? What do they start building first? How much of the logic do they build? Do they go in layers? Do they just add a little bit of code to every file first? I don't understand that part.

## 8

So unit testing is just like the logic and the structure of the code, essentially. You're just making sure that the code, the logic of the code works, okay? If this, then that. You know, like, if and then statements or whatever the hell they're called. You're making sure, like, the functions and classes, the logic is correct. It, you know, it returns true or false, it's correct. Units, good. Modular, good. So if you only have one module built out, you wouldn't possibly be able to do integration tests because there's nothing to integrate that module with. So then my next question is, once you build out, let's say, two modules, do you immediately want to, what do they do? Do they build out unit tests for the first, the very first module, make sure the unit tests are passing green, and then they build out the next module, and then they do unit tests, make sure they're passing green, and then they make an integration test at that point? Or does integration only come after all the unit tests, all the logic is built out? Or do they go module by module, file by file, units to integration, unit to integration, constantly backtracking? So if you build out two modules, you want to integrate the first one into the second one, and then you build out a third one, you want to do unit tests for the third one, and then finally you want to do integration with the first one, second one, into the third one, and then the fourth one, you want to do first, second, third, fourth, or is that technically becoming an end-to-end test at that point? Do end-to-end tests contain mocks in industry standards? They usually want to contain mocks, and for integration, do they want to contain mocks?

## 9

So you don't build end-to-end tests until essentially all files have been created, unit tested, and integrated, and integration tested, and are all passing and functioning. And then, only then, you make end-to-end tests that actually go through whether you use mock data or not for, you know, mocked API calls, etc., which I imagine is just for speed to use mocks as opposed to real end-to-end integration. But end-to-end doesn't come until everything is essentially unit tested and integrated and working.

## 10

Okay, then my next question is, I don't know why, but logging. I don't understand, do developers build out different levels of logging? I don't understand that. Or like, how does, you know, like, logging and PyTest. I don't know what I'm trying to ask you here, but they confuse me. Because in some of the projects I build with the AIs, they'll build out different levels to logging. Like, oh, this is your logs for debugging, or this is your logs for warnings, or this is your logs for errors, or this is your log for live mode, or this is your log for simulated mocks, or et cetera. It doesn't make sense to me.

## 11

Okay, but that's what I don't understand. How is it actually separated in your code? Like, how is, uh, testing logs and real, I don't even know, logs, how does, how does that even, how is that separate? Is it just simply enabled and disabled?

## 12

I still don't think I understand the logging concept when it comes to coding in terms of what we were talking about in this conversation.

## 13

## 14

So what's the difference from, like, doing a... running PyTest?

## 15

So logging is, I just want a short answer for this, logging is essentially only really for debugging something, like getting more information in terms of what the code is doing or what data it's pulling.

## 16

So how do you layer logging into a debugging setup? Like, if you're running PyTest, I know you said you can put logging into PyTest, but that seems weird. It sounds like more something you would use when you're debugging live, right? Because then, yeah. Or no.

## 17

So logging is just getting the nuance of the backend. So then there's different levels of logging, right? There's info logs, there's error logs, there's warning logs, there's what's common, or it's industry standard.

## 18

## 19

So in development, there's no logs, just like there's no debugging or testing done when an application is live. It's simply for the testing phase and figuring out what the code is doing, if it's working properly, if it's executing the right things.

## 20

Okay, so then in something like my Risk Manager, if I'm using events like SignalR to speak with my code, an info debug would be like, when I place a trade, I get a notification or a logging that the code captured the trade or was sent the trade. That'd be like an example, or like quote data. If I wanna see that, okay, yeah, the code is actually receiving or getting quotes or updating quotes, I would log quote info. So I see the repeated action of the quotes flowing in and out. Otherwise, you would have no idea to know that quotes are coming in or if you're getting your trade, if the trade is being sent or any of that stuff.

## 21

Because I think that's what I'm confused about is when I'm writing code or when I'm testing on my risk manager, when I'm debugging it or when I'm still testing it, it seems to go from PyTest to like just insane logging, just insane logging, and I kind of get confused because I'm getting like, okay, you've been authenticated, you're getting quotes, you're getting trades, you're getting all this stuff. That's not necessarily the deployment, that is just literally logging to debug and figure out what's happening, what's being sent, what the code's receiving, what it's sending back to the broker, etc. So then what you're saying is that a logger.py, for example, how does that work? Does it import modules from the rest of the code, and that's it? So you're in like the logger.py imports the rest of the code, and then you write out, how do you even write out a log, for example? You would write out the log, and then you would have to write the class or the function,

## 22

So you have a logger.py file, and you import that into the main code, like into your working code. Like, this isn't, it's not a, it's not a, you're not importing this into a test code. So you have your logger file, and then you import it into the working code, and then inside the logger.py file, is that where you turn on, like, enable debug, or disable warning, or enable this, or that.

## 23

Okay, so then in terms of, like, deployment, or, you know, dialing back the logs, you would have to go back into the main file and refractor, completely clean it up.

## 24

Or you could just turn them off, but if you want the code to be nice and structured and clean for deployment, then you would get rid of them.

## 25

Now, what does a logger.py file even consist of?

## 26

## 27

What’s the best language to use for this risk manager project ?

## 28

What are the most popular extensions of python industry standard

## 29

What is a daemon

## 30

I’m not using the sdk anymore btw, to complex

## 31

How can I trace better the actual actions. Like gclasses or functions? So classes we define forest like max_daily_loss_rule is a function or a class that we defined

## 32

How can I see the flow from one thing to the next, like I see a linear line of things being executed. These are classes or functions yes ? Max daily loss calls breach detector breach detector calls enforcement, enforcement send api request to close trade

## 33

How can u do that quickly without direct logging? Is that where coverage comes into play?

## 34

I like option 1 and 2. Visuals. This is called tracing? So dideerent than logging etc? Breakpoints would then be okay were tracing and then failure

## 35

So what extensions for tracing, what are popular?

## 36

Cause I’ll be trying to figure out why enforcement isn’t working or why my trade isn’t being sent to the code/not receiving events and I feel left in the dust? Ran a ton of pytest, all game back green, but no actions? Then I’m left thinking if only I could trace each call/method/function/class to see where and why it isn’t working… something more than pytest! Maybe that’s integration test error?

## 37

I’ve tried viztracer before but stopped because I couldn’t understand it. A ton of waves/colors/blocks, very confusing to read it

## 38

What if something that was intended to be called isn’t called, how would I know with a complex system ?

## 39

What is runtime?

## 40

Okay that seems huge then because I’m been struggling to discern this gap between writing test and then actual functional correct implantation of logic in a flow. So this is runtime, and we dont create more tests (or can we create integration test) we create runtime tracing? Am I getting that right or eh

## 41

So integration is the same as tracing?

## 42

Cause I’ll write integration and units, still get passing tests, but still no runtime execution. And then logging gets blown out of proportion and I can’t even tell why it ain’t working… I’m still a little stuck. We have a lot of terms like pytest, unit, integration, runtime, tracing etc. integration will be green but still nothing. No logging happens either. So I see how they all kind of play into each other but tracing feels most powerful why

## 43

[https://medium.com/@andrewh829/the-importance-of-code-tracing-solving-runtime-errors-b6377367b6b7](https://medium.com/@andrewh829/the-importance-of-code-tracing-solving-runtime-errors-b6377367b6b7)

## 44

What’s missing between integration and runtime tracing? Why do integration tests go green but nothing on run? Whats the cause of that

## 45

What’s a smoke test

## 46

Wb timing? I think about a code project, something like mine (not using async anymore btw) there’s thousands of lines of code, how do I know they’re being executed in the proper sequence? I guess this goes back to runtime trading

## 47

I’m just trying to get to the core of what to do when tests are green and nothing occurs when and where and how I wanted it to.. it’s extremely frustrating. More tests and more logging is slow and never seems to help with it.
