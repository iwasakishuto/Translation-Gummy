# coding: utf-8

# Journal Data.
JournalData = dict(
    arxiv="https://arxiv.org/abs/2003.03253",
    nature="https://doi.org/10.1038/171737a0",
    pubmed="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5325678/",
)
JournalData = {journal.lower():url for journal,url in JournalData.items()}

# Sentence Data
SentenceData = dict(
    simple_sentence    = "This is a pen.",
    multiple_sentences = "I have a pen. I have an apple. Ah, apple pen.",
    SteveJobsSpeech    = "Thank You. I am honored to be with you today for your commencement from one of the finest universities in the world. Truth be told I never graduated from college and this is the closest I’ve ever gotten to a college graduation. Today I want to tell you three stories from my life. That’s it. No big deal. Just three stories. The first story is about connecting the dots. I dropped out of Reed College after the first 6 months, but then stayed around as a drop-in for another 18 months or so before I really quit. So why did I drop out? It started before I was born. My biological mother was a young, unwed graduate student, and she decided to put me up for adoption. She felt very strongly that I should be adopted by college graduates, so everything was all set for me to be adopted at birth by a lawyer and his wife. Except that when I popped out they decided at the last minute that they really wanted a girl. So my parents, who were on a waiting list, got a call in the middle of the night asking: “We’ve got an unexpected baby boy; do you want him?” They said: “Of course.” My biological mother found out later that my mother had never graduated from college and that my father had never graduated from high school. She refused to sign the final adoption papers. She only relented a few months later when my parents promised that I would go to college. This was the start in my life. And 17 years later I did go to college. But I naively chose a college that was almost as expensive as Stanford, and all of my working-class parents’ savings were being spent on my college tuition. After six months, I couldn’t see the value in it. I had no idea what I wanted to do with my life and no idea how college was going to help me figure it out. And here I was spending all of the money my parents had saved their entire life. So I decided to drop out and trust that it would all work out OK. It was pretty scary at the time, but looking back it was one of the best decisions I ever made. The minute I dropped out I could stop taking the required classes that didn’t interest me, and begin dropping in on the ones that looked far more interesting. It wasn’t all romantic. I didn’t have a dorm room, so I slept on the floor in friends’ rooms, I returned coke bottles for the 5 cent deposits to buy food with, and I would walk the 7 miles across town every Sunday night to get one good meal a week at the Hare Krishna temple. I loved it. And much of what I stumbled into by following my curiosity and intuition turned out to be priceless later on. Let me give you one example: Reed College at that time offered perhaps the best calligraphy instruction in the country. Throughout the campus every poster, every label on every drawer, was beautifully hand calligraphed. Because I had dropped out and didn’t have to take the normal classes, I decided to take a calligraphy class to learn how to do this. I learned about serif and sans-serif typefaces, about varying the amount of space between different letter combinations, about what makes great typography great. It was beautiful, historical, artistically subtle in a way that science can’t capture, and I found it fascinating. None of this had even a hope of any practical application in my life. But ten years later, when we were designing the first Macintosh computer, it all came back to me. And we designed it all into the Mac. It was the first computer with beautiful typography. If I had never dropped in on that single course in college, the Mac would have never had multiple typefaces or proportionally spaced fonts. And since Windows just copied the Mac, it’s likely that no personal computer would have them. If I had never dropped out, I would have never dropped in on that calligraphy class, and personal computers might not have the wonderful typography that they do. Of course it was impossible to connect the dots looking forward when I was in college. But it was very, very clear looking backward ten years later. Again, you can’t connect the dots looking forward; you can only connect them looking backward. So you have to trust that the dots will somehow connect in your future. You have to trust in something, your gut, destiny, life, karma, whatever. Because believing that the dots will connect down the road will give you the confidence to follow your heart. Even when it leads you off the well-worn path, and that will make all the difference."
)


# Save as db.
class TestData():
    def __init__(self):
        self.journals = JournalData
        self.sentences = SentenceData

    def insert_journal(self, journal, url):
        self.journals[journal] = url

    def get_journal(self, journal):
        return self.journals.get(journal)

    def iter_data(self, data_type):
        for key,value in self.__dict__.get(data_type).items():
            yield key,value
