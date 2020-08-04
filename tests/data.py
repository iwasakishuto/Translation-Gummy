# coding: utf-8

# Journal Data.
JournalData = {
	"NCBI"             : "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1573881/",
	"OxfordAcademic"   : "https://academic.oup.com/endo/article/144/11/5118/2881228",
	"ScienceDirect"    : "https://www.sciencedirect.com/science/article/abs/pii/S0006291X00924586?via%3Dihub",
	"Springer"         : "https://link.springer.com/article/10.1023/A:1009641613826",
	"Nature"           : "https://www.nature.com/articles/ncb0800_500",
	"MDPI"             : "https://www.mdpi.com/1422-0067/14/6/11171",
	"ieee"             : "https://ieeexplore.ieee.org/document/4752474",
	"JBC"              : "https://www.jbc.org/content/280/13/12967",
	"PLOSONE"          : "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0028688",
	"Wiley"            : "https://onlinelibrary.wiley.com/doi/abs/10.1002/arch.20006",
	"frontiers"        : "https://www.frontiersin.org/articles/10.3389/fgene.2012.00101/full",
	"JSTAGE"           : "https://www.jstage.jst.go.jp/article/jnms/77/2/77_2_71/_article",
	"TandFOnline"      : "https://www.tandfonline.com/doi/full/10.1080/15476286.2018.1486658",
	"ACS"              : "https://pubs.acs.org/doi/10.1021/nl101829m",
	"Biologists"       : "https://dev.biologists.org/content/132/11/2547",
	"FEBS"             : "https://febs.onlinelibrary.wiley.com/doi/full/10.1016/S0014-5793%2800%2901883-4",
	"LungCancer"       : "https://www.lungcancerjournal.info/article/S0169-5002(02)00218-0/fulltext",
	"Spandidos"        : "https://www.spandidos-publications.com/10.3892/ijmm.2015.2141",
	"BMC"              : "https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-10-392",
	"UniOKLAHOMA"      : "https://www.ou.edu/journals/dis/DIS83/Technique83/7tecUiTei/UiTei.htm",
	"NRCResearchPress" : "https://www.nrcresearchpress.com/doi/10.1139/gen-2016-0127",
	"Biologists"       : "https://jcs.biologists.org/content/127/8/1805",
	"UniKeio"          : "https://keio.pure.elsevier.com/ja/publications/enhanced-specificity-of-hpv16-e6e7-sirna-by-rna-dna-chimera-modif",
	"ScienceDirect"    : "https://linkinghub.elsevier.com/retrieve/pii/S0022283617301936",
	"IntechOpen"       : "https://www.intechopen.com/books/gene-expression-and-regulation-in-mammalian-cells-transcription-from-general-aspects/current-status-for-application-of-rna-interference-technology-as-nucleic-acid-drug",
	"PubMed"           : "https://pubmed.ncbi.nlm.nih.gov/15125233/",
	"CellPress"        : "https://www.cell.com/fulltext/S0960-9822(02)01394-5",
	"Biologists"       : "https://bio.biologists.org/content/9/2/bio050435",
	"RNAjournal"       : "https://rnajournal.cshlp.org/content/19/1/17",
	"StemCells"        : "https://stemcellsjournals.onlinelibrary.wiley.com/doi/full/10.1002/stem.615",
	"bioRxiv"          : "https://www.biorxiv.org/content/10.1101/724575v1",
	"RSC"              : "https://pubs.rsc.org/en/content/articlelanding/2004/CS/b303644h",
	"JSSE"             : "https://www.jsse.org/index.php/jsse/article/view/531/528",
	"ScienceAdvances"  : "https://advances.sciencemag.org/content/6/20/eaaz6485",
	"medRxiv"          : "https://www.medrxiv.org/content/10.1101/2020.04.21.20074567v2",
	"ACLAnthology"     : "https://www.aclweb.org/anthology/2020.acl-main.28",
	"PNAS"             : "https://www.pnas.org/content/113/20/5498",
}
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
