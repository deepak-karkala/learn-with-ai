// Mock remark-gfm plugin
const remarkGfm = () => {
  return (tree) => tree;
};

module.exports = remarkGfm;
module.exports.default = remarkGfm;