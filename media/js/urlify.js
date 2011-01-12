var LATIN_MAP = {
    'Ã€': 'A', 'Ã': 'A', 'Ã‚': 'A', 'Ãƒ': 'A', 'Ã„': 'A', 'Ã…': 'A', 'Ã†': 'AE', 'Ã‡':
    'C', 'Ãˆ': 'E', 'Ã‰': 'E', 'ÃŠ': 'E', 'Ã‹': 'E', 'ÃŒ': 'I', 'Ã': 'I', 'ÃŽ': 'I',
    'Ã': 'I', 'Ã': 'D', 'Ã‘': 'N', 'Ã’': 'O', 'Ã“': 'O', 'Ã”': 'O', 'Ã•': 'O', 'Ã–':
    'O', 'Å': 'O', 'Ã˜': 'O', 'Ã™': 'U', 'Ãš': 'U', 'Ã›': 'U', 'Ãœ': 'U', 'Å°': 'U',
    'Ã': 'Y', 'Ãž': 'TH', 'ÃŸ': 'ss', 'Ã ':'a', 'Ã¡':'a', 'Ã¢': 'a', 'Ã£': 'a', 'Ã¤':
    'a', 'Ã¥': 'a', 'Ã¦': 'ae', 'Ã§': 'c', 'Ã¨': 'e', 'Ã©': 'e', 'Ãª': 'e', 'Ã«': 'e',
    'Ã¬': 'i', 'Ã­': 'i', 'Ã®': 'i', 'Ã¯': 'i', 'Ã°': 'd', 'Ã±': 'n', 'Ã²': 'o', 'Ã³':
    'o', 'Ã´': 'o', 'Ãµ': 'o', 'Ã¶': 'o', 'Å‘': 'o', 'Ã¸': 'o', 'Ã¹': 'u', 'Ãº': 'u',
    'Ã»': 'u', 'Ã¼': 'u', 'Å±': 'u', 'Ã½': 'y', 'Ã¾': 'th', 'Ã¿': 'y'
}
var LATIN_SYMBOLS_MAP = {
    'Â©':'(c)'
}
var GREEK_MAP = {
    'Î±':'a', 'Î²':'b', 'Î³':'g', 'Î´':'d', 'Îµ':'e', 'Î¶':'z', 'Î·':'h', 'Î¸':'8',
    'Î¹':'i', 'Îº':'k', 'Î»':'l', 'Î¼':'m', 'Î½':'n', 'Î¾':'3', 'Î¿':'o', 'Ï€':'p',
    'Ï':'r', 'Ïƒ':'s', 'Ï„':'t', 'Ï…':'y', 'Ï†':'f', 'Ï‡':'x', 'Ïˆ':'ps', 'Ï‰':'w',
    'Î¬':'a', 'Î­':'e', 'Î¯':'i', 'ÏŒ':'o', 'Ï':'y', 'Î®':'h', 'ÏŽ':'w', 'Ï‚':'s',
    'ÏŠ':'i', 'Î°':'y', 'Ï‹':'y', 'Î':'i',
    'Î‘':'A', 'Î’':'B', 'Î“':'G', 'Î”':'D', 'Î•':'E', 'Î–':'Z', 'Î—':'H', 'Î˜':'8',
    'Î™':'I', 'Îš':'K', 'Î›':'L', 'Îœ':'M', 'Î':'N', 'Îž':'3', 'ÎŸ':'O', 'Î ':'P',
    'Î¡':'R', 'Î£':'S', 'Î¤':'T', 'Î¥':'Y', 'Î¦':'F', 'Î§':'X', 'Î¨':'PS', 'Î©':'W',
    'Î†':'A', 'Îˆ':'E', 'ÎŠ':'I', 'ÎŒ':'O', 'ÎŽ':'Y', 'Î‰':'H', 'Î':'W', 'Îª':'I',
    'Î«':'Y'
}
var TURKISH_MAP = {
    'ÅŸ':'s', 'Åž':'S', 'Ä±':'i', 'Ä°':'I', 'Ã§':'c', 'Ã‡':'C', 'Ã¼':'u', 'Ãœ':'U',
    'Ã¶':'o', 'Ã–':'O', 'ÄŸ':'g', 'Äž':'G'
}
var RUSSIAN_MAP = {
    'Ð°':'a', 'Ð±':'b', 'Ð²':'v', 'Ð³':'g', 'Ð´':'d', 'Ðµ':'e', 'Ñ‘':'yo', 'Ð¶':'zh',
    'Ð·':'z', 'Ð¸':'i', 'Ð¹':'j', 'Ðº':'k', 'Ð»':'l', 'Ð¼':'m', 'Ð½':'n', 'Ð¾':'o',
    'Ð¿':'p', 'Ñ€':'r', 'Ñ':'s', 'Ñ‚':'t', 'Ñƒ':'u', 'Ñ„':'f', 'Ñ…':'h', 'Ñ†':'c',
    'Ñ‡':'ch', 'Ñˆ':'sh', 'Ñ‰':'sh', 'ÑŠ':'', 'Ñ‹':'y', 'ÑŒ':'', 'Ñ':'e', 'ÑŽ':'yu',
    'Ñ':'ya',
    'Ð':'A', 'Ð‘':'B', 'Ð’':'V', 'Ð“':'G', 'Ð”':'D', 'Ð•':'E', 'Ð':'Yo', 'Ð–':'Zh',
    'Ð—':'Z', 'Ð˜':'I', 'Ð™':'J', 'Ðš':'K', 'Ð›':'L', 'Ðœ':'M', 'Ð':'N', 'Ðž':'O',
    'ÐŸ':'P', 'Ð ':'R', 'Ð¡':'S', 'Ð¢':'T', 'Ð£':'U', 'Ð¤':'F', 'Ð¥':'H', 'Ð¦':'C',
    'Ð§':'Ch', 'Ð¨':'Sh', 'Ð©':'Sh', 'Ðª':'', 'Ð«':'Y', 'Ð¬':'', 'Ð­':'E', 'Ð®':'Yu',
    'Ð¯':'Ya'
}
var UKRAINIAN_MAP = {
    'Ð„':'Ye', 'Ð†':'I', 'Ð‡':'Yi', 'Ò':'G', 'Ñ”':'ye', 'Ñ–':'i', 'Ñ—':'yi', 'Ò‘':'g'
}
var CZECH_MAP = {
    'Ä':'c', 'Ä':'d', 'Ä›':'e', 'Åˆ': 'n', 'Å™':'r', 'Å¡':'s', 'Å¥':'t', 'Å¯':'u',
    'Å¾':'z', 'ÄŒ':'C', 'ÄŽ':'D', 'Äš':'E', 'Å‡': 'N', 'Å˜':'R', 'Å ':'S', 'Å¤':'T',
    'Å®':'U', 'Å½':'Z'
}

var POLISH_MAP = {
    'Ä…':'a', 'Ä‡':'c', 'Ä™':'e', 'Å‚':'l', 'Å„':'n', 'Ã³':'o', 'Å›':'s', 'Åº':'z',
    'Å¼':'z', 'Ä„':'A', 'Ä†':'C', 'Ä˜':'e', 'Å':'L', 'Åƒ':'N', 'Ã“':'o', 'Åš':'S',
    'Å¹':'Z', 'Å»':'Z'
}

var LATVIAN_MAP = {
    'Ä':'a', 'Ä':'c', 'Ä“':'e', 'Ä£':'g', 'Ä«':'i', 'Ä·':'k', 'Ä¼':'l', 'Å†':'n',
    'Å¡':'s', 'Å«':'u', 'Å¾':'z', 'Ä€':'A', 'ÄŒ':'C', 'Ä’':'E', 'Ä¢':'G', 'Äª':'i',
    'Ä¶':'k', 'Ä»':'L', 'Å…':'N', 'Å ':'S', 'Åª':'u', 'Å½':'Z'
}

var ALL_DOWNCODE_MAPS=new Array()
ALL_DOWNCODE_MAPS[0]=LATIN_MAP
ALL_DOWNCODE_MAPS[1]=LATIN_SYMBOLS_MAP
ALL_DOWNCODE_MAPS[2]=GREEK_MAP
ALL_DOWNCODE_MAPS[3]=TURKISH_MAP
ALL_DOWNCODE_MAPS[4]=RUSSIAN_MAP
ALL_DOWNCODE_MAPS[5]=UKRAINIAN_MAP
ALL_DOWNCODE_MAPS[6]=CZECH_MAP
ALL_DOWNCODE_MAPS[7]=POLISH_MAP
ALL_DOWNCODE_MAPS[8]=LATVIAN_MAP

var Downcoder = new Object();
Downcoder.Initialize = function()
{
    if (Downcoder.map) // already made
        return ;
    Downcoder.map ={}
    Downcoder.chars = '' ;
    for(var i in ALL_DOWNCODE_MAPS)
    {
        var lookup = ALL_DOWNCODE_MAPS[i]
        for (var c in lookup)
        {
            Downcoder.map[c] = lookup[c] ;
            Downcoder.chars += c ;
        }
     }
    Downcoder.regex = new RegExp('[' + Downcoder.chars + ']|[^' + Downcoder.chars + ']+','g') ;
}

downcode= function( slug )
{
    Downcoder.Initialize() ;
    var downcoded =""
    var pieces = slug.match(Downcoder.regex);
    if(pieces)
    {
        for (var i = 0 ; i < pieces.length ; i++)
        {
            if (pieces[i].length == 1)
            {
                var mapped = Downcoder.map[pieces[i]] ;
                if (mapped != null)
                {
                    downcoded+=mapped;
                    continue ;
                }
            }
            downcoded+=pieces[i];
        }
    }
    else
    {
        downcoded = slug;
    }
    return downcoded;
}


function URLify(s, num_chars) {
    // changes, e.g., "Petty theft" to "petty_theft"
    // remove all these words from the string before urlifying
    s = downcode(s);
    removelist = ["a", "an", "as", "at", "before", "but", "by", "for", "from",
                  "is", "in", "into", "like", "of", "off", "on", "onto", "per",
                  "since", "than", "the", "this", "that", "to", "up", "via",
                  "with"];
    r = new RegExp('\\b(' + removelist.join('|') + ')\\b', 'gi');
    s = s.replace(r, '');
    // if downcode doesn't hit, the char will be stripped here
    s = s.replace(/[^-\w\s]/g, '');  // remove unneeded chars
    s = s.replace(/^\s+|\s+$/g, ''); // trim leading/trailing spaces
    s = s.replace(/[-\s]+/g, '-');   // convert spaces to hyphens
    s = s.toLowerCase();             // convert to lowercase
    return s.substring(0, num_chars);// trim to first num_chars chars
}

function DPSlugify(s, num_chars) {
    // changes, e.g., "Petty theft" to "petty_theft"
    // remove all these words from the string before urlifying
    s = downcode(s);
    r = new RegExp('\\b(' + ')\\b', 'gi');
    s = s.replace(r, '');
    // if downcode doesn't hit, the char will be stripped here
    s = s.replace(/[^-\w\s]/g, '');  // remove unneeded chars
    s = s.replace(/^\s+|\s+$/g, ''); // trim leading/trailing spaces
    s = s.replace(/[-\s]+/g, '-');   // convert spaces to hyphens
    s = s.toLowerCase();             // convert to lowercase
    return s.substring(0, num_chars);// trim to first num_chars chars
}
