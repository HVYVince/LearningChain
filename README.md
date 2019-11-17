## Inspiration

As machine learning requires more and more computing **power**, people turn to services such as **AWS**, **Google Cloud**, or similar to train tedious machine learning algorithms.

While those services are **nice**, they are also **pricey** and you have to resolve that your data will be detained by **big companies**...

## What it does

_LearningChain_ creates a **network of computers** (the _graph_) running its client that allows individuals as well as universities and companies to share their computing power in a fair way, in order to be able to make **others** do computations for **you**. 

Although the service is **completely free**, you need to make computations for someone else **first** to acquire **credits** that will allow you to submit **your own task** to the graph.

When a task is submitted, **every client** can grab it, but only the **best answer** will receive the credits for it.

## How we built it

We chose the **blockchain technology** to have a **complete history** of all that happen over the network, as well as to **manage the credit system**. A python client takes care of **handling data** from the blockchain : it receives a new job from the graph, runs it, then **announces its result** to the network, and if it is the best one, **gets paid** and **returns the computed model** back to the contractor.

In order to **avoid harmful code** to be executed on your computer, the learning is done **in isolation** in a docker container that can **not access the internet** nor **any other resource** that may exist in your computer and that was not included in the contract. 

## Getting technical

So here is exactly what happens when you want to use our service.
1. You download our client and run it. It will generate an ECC key pair that will **uniquely** identify yourself on the graph
2. You configure the client to run only jobs that **you have interests in** : validity date far enough, bounty high enough, and let it run until you've acquired enough credits.
3. You create a docker container with everything your model needs for its training. You host it on the container host of **your choice**. 
4. You create the job with the bounty you are ready to pay for its completion. The **higher the bounty**, the more the graph is interested in your job, and **the faster the result arrive** !
5. Your job is propagated on the graph and the bounty taken out of your balance. 
6. As soon as **a node founds a solution**, it propagates it to the network, announcing the computed loss.
7. Anyone can still try to **beat** that announced loss until the expiration date of your job.
8. When your job expires, the node that gave the best loss **wins** the bounty. The news is propagated on the graph. If more than one node have the exact same loss, **the fastest one wins**.
9. The winner propagates the computed model on the graph.
10. Every node can **check** whether the winner lied on the announced loss by trying the proposed model. If enough node consider the winner to be a cheater, it is **banned** from the graph and its credits are lost. If this is the case, **your bounty is then returned to you**.

## Challenges we ran into

Building a blockchain from scratch is **hard**, **really hard**, and we had to solve a lot of issues towards a blockchain systems that is **resilient** to **malfunctioning nodes** as well as **malicious ones**. It took a long time designing a protocol we can **trust** over the graph before we reached a consensus.
 
After designing, implementation was **interminable**. It took us **all night** to code every aspect of our proof-of-concept, but we are **proud** of the result.

## Accomplishments that we're proud of

Well most basic one is : **we've done it** ! Really, the coding power of 4 motivated guys during more than 20 hours was the very minimum we could have performed such a task with.

We also are **thrilled** by the whole protocol we came with. Of course we have **no proof** it is truly safe, but we believe that **all the most basic attacks** you can think of will be **unexploitable** on LearningChain's network.

## What we learned

This project forced us to **tackle** many problems we were **unaware of** when designing a **decentralized distributed system**. It also taught us that sometimes, the solution is so **simple** that the only way to see it is to **take a step back** and rethink everything.

## What's next for LearningChain

Well, this is still a proof of concept. We would need to actually develop a node communication protocol for the blockchain and a discovery service, and we would also need a thorough test of the network to be sure everything is as secure as we can make it.

## Sponsor challenges we apply to

We decided to tackle the challenge issued by AdNovum
