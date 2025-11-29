#ifndef PCER_HELPER_H
#define PCER_HELPER_H

#include "ns3/ipv4-list-routing.h"
#include "ns3/ipv4-routing-helper.h"
#include "ns3/node-container.h"
#include "pcer-routing-protocol.h"

namespace ns3 {

class PcerHelper : public Ipv4RoutingHelper {
public:
  PcerHelper() {}

  PcerHelper *Copy(void) const { return new PcerHelper(*this); }

  virtual Ptr<Ipv4RoutingProtocol> Create(Ptr<Node> node) const {
    return CreateObject<PcerRoutingProtocol>();
  }
};

} // namespace ns3

#endif /* PCER_HELPER_H */
